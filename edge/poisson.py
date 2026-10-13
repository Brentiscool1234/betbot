"""Experimental independent-Poisson baseline; no validated profitability claim."""
import math
from .store import digest, timestamp

MODEL_VERSION='poisson-venue-v1'
CONFIG={'model_version':MODEL_VERSION,'min_league_matches':50,'min_team_venue_matches':5,'prior_matches':5,'team_window':20}


def distribution(rate):
    if not math.isfinite(rate) or not 0<=rate<=100:
        raise ValueError('invalid goal rate')
    probabilities=[math.exp(-rate)]
    for k in range(1,513):
        probabilities.append(probabilities[-1]*rate/k)
        if k>rate and 1-sum(probabilities)<1e-12: break
    if 1-sum(probabilities)>1e-10: raise ValueError('score distribution tail too large')
    return probabilities


def probabilities(home_rate,away_rate):
    home=distribution(home_rate); away=distribution(away_rate)
    output={'home':0.0,'draw':0.0,'away':0.0}
    for h,ph in enumerate(home):
        for a,pa in enumerate(away):
            output['home' if h>a else 'away' if h<a else 'draw']+=ph*pa
    total=sum(output.values())
    return {k:v/total for k,v in output.items()}


def states_at(records,as_of):
    cutoff=timestamp(as_of); latest={}
    for r in records:
        if max(r['available_at'],r['effective_at'],r['observed_at'])>cutoff: continue
        key=(r['match_id'],r['kind'],r['key'])
        order=(r['available_at'],r['effective_at'],r['observed_at'],digest(r))
        if key not in latest or order>latest[key][0]: latest[key]=(order,r)
    states={}
    for (mid,kind,key),(_,r) in sorted(latest.items()): states.setdefault(mid,[]).append(r)
    return states


def predict(states,match_id,as_of,config=None):
    config=dict(CONFIG if config is None else config)
    cutoff=timestamp(as_of)
    fixture=next((r for r in states.get(match_id,[]) if r['kind']=='fixture'),None)
    if fixture is not None and max(fixture['available_at'],fixture['effective_at'],fixture['observed_at'])>cutoff:
        fixture=None
    if fixture is None: return {'status':'insufficient_data','reason':'fixture unavailable'}
    target=fixture['payload']; target_kickoff=timestamp(target['kickoff'])
    if target_kickoff<=cutoff: return {'status':'unavailable','reason':'match already started'}
    history=[]
    for mid,rows in states.items():
        if mid==match_id: continue
        f=next((r for r in rows if r['kind']=='fixture'),None); result=next((r for r in rows if r['kind']=='result'),None)
        if not f or not result: continue
        if max(f['available_at'],f['effective_at'],f['observed_at'],result['available_at'],result['effective_at'],result['observed_at'])>cutoff: continue
        p=f['payload']
        if p['competition_id']!='soccer_epl' or timestamp(p['kickoff'])>=min(cutoff,target_kickoff): continue
        if result['payload']['status']!='finished' or result['effective_at']<timestamp(p['kickoff']): continue
        history.append((timestamp(p['kickoff']),mid,f,result))
    history.sort(reverse=True,key=lambda item:(item[0],item[1]))
    home_history=[x for x in history if x[2]['payload']['home_team']==target['home_team']][:config['team_window']]
    away_history=[x for x in history if x[2]['payload']['away_team']==target['away_team']][:config['team_window']]
    counts={'league':len(history),'home_team_at_home':len(home_history),'away_team_away':len(away_history)}
    if len(history)<config['min_league_matches'] or min(len(home_history),len(away_history))<config['min_team_venue_matches']:
        return {'status':'insufficient_data','reason':'not enough point-in-time league/team results','history_counts':counts}
    league_home=sum(x[3]['payload']['home_goals'] for x in history)/len(history)
    league_away=sum(x[3]['payload']['away_goals'] for x in history)/len(history)
    if min(league_home,league_away)<=0: return {'status':'insufficient_data','reason':'zero league scoring baseline','history_counts':counts}
    prior=config['prior_matches']
    def mean(rows,key,baseline): return (sum(x[3]['payload'][key] for x in rows)+prior*baseline)/(len(rows)+prior)
    home_attack=mean(home_history,'home_goals',league_home)/league_home
    home_defence=mean(home_history,'away_goals',league_away)/league_away
    away_attack=mean(away_history,'away_goals',league_away)/league_away
    away_defence=mean(away_history,'home_goals',league_home)/league_home
    home_rate=league_home*home_attack*away_defence
    away_rate=league_away*away_attack*home_defence
    sources=sorted({digest(r) for x in history for r in x[2:]})
    return {'status':'experimental_prediction','model_version':MODEL_VERSION,'model_config':config,'config_hash':digest(config),
            'lambda_home':home_rate,'lambda_away':away_rate,'probabilities':probabilities(home_rate,away_rate),
            'history_counts':counts,'source_records':sources,'fixture_record':digest(fixture)}
