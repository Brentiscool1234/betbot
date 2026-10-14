"""Prospective integration of the frozen research proposal; experimental only."""
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from .store import timestamp,digest
from .elo import Elo,blend
from .form import Form
ELO_CONFIG=json.loads(Path(__file__).with_name("elo_config.json").read_text())
from .research.dynamic import Dynamic,temperature,residual_proposal,SIDES

CONFIG=json.loads(Path(__file__).with_name('research').joinpath('live_config.json').read_text())
MODEL_VERSION=CONFIG['version']


def prepare(states,as_of):
    cutoff=timestamp(as_of); grouped={}
    for mid,rows in states.items():
        f=next((r for r in rows if r['kind']=='fixture'),None); score=next((r for r in rows if r['kind']=='result'),None)
        if not f or not score: continue
        if max(f['available_at'],f['observed_at'],f['effective_at'],score['available_at'],score['observed_at'],score['effective_at'])>cutoff: continue
        p=f['payload']; kickoff=timestamp(p['kickoff'])
        if p['competition_id']!='soccer_epl' or kickoff>=cutoff or score['effective_at']<kickoff: continue
        if score['payload']['status']!='finished': continue
        day=datetime.fromisoformat(kickoff).astimezone(ZoneInfo('Europe/London')).date().isoformat()
        grouped.setdefault((p['home_team'],p['away_team'],day),[]).append((kickoff,mid,f,score))
    history=[]; conflicts=0
    for entries in grouped.values():
        if len({(e[3]['payload']['home_goals'],e[3]['payload']['away_goals']) for e in entries})>1:
            conflicts+=1; continue
        history.append(max(entries,key=lambda e:(e[3]['source']=='the-odds-api',e[3]['available_at'],e[1])))
    history.sort(key=lambda e:(e[0],e[1])); form=Form(); elo=Elo(**{k:ELO_CONFIG[k] for k in ('k','home_advantage','draw_parameter')}); models=[Dynamic(**c) for c in CONFIG['adaptation_configs']]
    for kickoff,mid,f,score in history:
        day=datetime.fromisoformat(kickoff).astimezone(ZoneInfo('Europe/London')).date().isoformat()
        form.observe(f['payload']['home_team'],f['payload']['away_team'],score['payload']['home_goals'],score['payload']['away_goals'])
        elo.observe(f['payload']['home_team'],f['payload']['away_team'],score['payload']['home_goals'],score['payload']['away_goals'])
        for model in models: model.observe(f['payload']['home_team'],f['payload']['away_team'],day,score['payload']['home_goals'],score['payload']['away_goals'])
    return {'form':form,'elo':elo,'models':models,'history':history,'conflicts':conflicts,'as_of':cutoff}


def predict(states,match_id,as_of,prices,context=None):
    context=context or prepare(states,as_of); cutoff=timestamp(as_of)
    if context['as_of']!=cutoff: raise ValueError('training context cutoff mismatch')
    fixture=next((r for r in states.get(match_id,[]) if r['kind']=='fixture'),None)
    if not fixture or max(fixture['available_at'],fixture['effective_at'],fixture['observed_at'])>cutoff: return {'status':'insufficient_data','reason':'fixture unavailable'}
    f=fixture['payload']
    if timestamp(f['kickoff'])<=cutoff: return {'status':'unavailable','reason':'match already started'}
    day=datetime.fromisoformat(cutoff).astimezone(ZoneInfo('Europe/London')).date().isoformat()
    forecasts=[m.forecast(f['home_team'],f['away_team'],day) for m in context['models']]
    h=context['history']; home=forecasts[0]['home_history']; away=forecasts[0]['away_history']
    counts={'league':len(h),'home_team_total':home,'away_team_total':away,'minimum_team_matches':5,
            'home_team_at_home':sum(e[2]['payload']['home_team']==f['home_team'] for e in h),
            'away_team_away':sum(e[2]['payload']['away_team']==f['away_team'] for e in h),'conflicting_events_excluded':context['conflicts']}
    if len(h)<50 or min(home,away)<5:
        return {'status':'insufficient_data','reason':'need 50 observed league results and five prior EPL results for each team','history_counts':counts,'model_version':MODEL_VERSION}
    members=[temperature(p['probabilities'],t) for p,t in zip(forecasts,CONFIG['temperatures'])]
    football={k:sum(w*p[k] for w,p in zip(CONFIG['weights'],members)) for k in SIDES}
    output={'status':'experimental_prediction','model_version':MODEL_VERSION,'model_config':CONFIG,'config_hash':digest(CONFIG),
            'history_counts':counts,'football_probabilities':football,'probabilities':football,
            'lambda_home':sum(w*p['lambda_home'] for w,p in zip(CONFIG['weights'],forecasts)),
            'lambda_away':sum(w*p['lambda_away'] for w,p in zip(CONFIG['weights'],forecasts)),
            'source_records':sorted({digest(r) for e in h for r in e[2:]}),'fixture_record':digest(fixture),
            'probability_basis':'market_adjusted' if prices['status']=='available' else 'football_only_missing_market','market_anchor_available':prices['status']=='available','validation_status':'experimental; prospective accuracy unverified'}
    elo=context['elo'].forecast(f['home_team'],f['away_team'])
    output.update(recent_form={'home':context['form'].summary(f['home_team']),'away':context['form'].summary(f['away_team'])},elo=elo,winner_probabilities=blend(football,elo['probabilities'],ELO_CONFIG['blend_weight']),winner_model_version=ELO_CONFIG['version'],winner_config_hash=digest(ELO_CONFIG),elo_config=ELO_CONFIG)
    if prices['status']=='available':
        proposal=residual_proposal(prices['consensus'],members,CONFIG['weights'],min(home,away),{k:p['decimal_odds'] for k,p in prices['best_prices'].items()})
        output.update(probabilities=proposal['probabilities'],market_residual_weight=proposal['market_residual_weight'],
                      model_disagreement=proposal['model_disagreement'],scenario_minimum_estimated_ev=proposal['scenario_minimum_estimated_ev'])
    return output
