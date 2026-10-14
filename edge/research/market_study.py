"""Bounded retrospective market benchmarking; no historical results PIT claim."""
import argparse
import json
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from collections import defaultdict
from pathlib import Path
from .compare import load,Venue,CONFIGS,score,block_interval
from .dynamic import Dynamic,temperature,residual_proposal,SIDES
from ..provider import fetch,archive,load_archive,convert,atomic_json
from ..store import timestamp,digest,now
from ..budget import Budget


def run(directory='data/research/dynamic-v1',target=100,max_requests=20):
    if not 1<=max_requests<=20 or not 1<=target<=100: raise ValueError('study bounds are 1..20 requests and 1..100 fixtures')
    directory=Path(directory)
    report=json.loads((directory/'report.json').read_text()); matches,hashes=load(directory/'inputs')
    if hashes!=report['source_hashes']: raise ValueError('result source hashes differ from registered comparison')
    by_key={}
    for m in matches:
        key=(m['home'],m['away'],m['day'])
        if key in by_key: raise ValueError('ambiguous result mapping')
        by_key[key]=m
    cache=directory/'market-archives'; cache.mkdir(parents=True,exist_ok=True)
    budget_path=directory/'market-credit-budget.json'
    if not budget_path.exists():
        current=datetime.now(timezone.utc); day=current.strftime('%Y-%m-%d'); month=current.strftime('%Y-%m')
        daily=monthly=0
        for path in cache.glob('*.json'):
            e=load_archive(path); cost=int(e['quota'].get('last') or 10)
            if e['received_at'][:10]==day: daily+=cost
            if e['received_at'][:7]==month: monthly+=cost
        atomic_json(budget_path,{'day':day,'month':month,'daily_used':daily,'monthly_used':monthly})
    budget=Budget(budget_path,daily=200,monthly=200)
    collected={}; calls=0
    for i in range(max_requests):
        requested=(datetime(2025,8,8,12,tzinfo=timezone.utc)+timedelta(days=7*i)).strftime('%Y-%m-%dT%H:%M:%SZ')
        pointer=cache/f'snapshot-{i:02d}.pointer'
        if pointer.exists(): envelope=load_archive(cache/(pointer.read_text().strip()+'.json'))
        else:
            blocked=budget.reserve(datetime.now(timezone.utc),cost=10)
            if blocked: raise ValueError('Historical research budget: '+blocked)
            envelope=fetch('historical/sports/soccer_epl/odds',{'regions':'uk','markets':'h2h','oddsFormat':'decimal','date':requested})
            budget.reconcile(envelope['quota'],reserved=10)
            sha=archive(cache,envelope); pointer.write_text(sha+'\n'); calls+=1
        snapshot=timestamp(envelope['response']['timestamp']); snapdate=datetime.fromisoformat(snapshot).date()
        # Conservative hypothetical availability; no production observed timestamps changed.
        training=[m for m in matches if datetime.fromisoformat(m['day']).date()<=snapdate-timedelta(days=3)]
        models=[Dynamic(**c) for c in CONFIGS]; venue=Venue()
        for m in training:
            for model in models: model.observe(m['home'],m['away'],m['day'],m['hg'],m['ag'])
            venue.history.append(m)
        groups=defaultdict(list)
        for r in convert(envelope,historical=True): groups[r['match_id']].append(r)
        for mid,rows in sorted(groups.items()):
            if mid in collected: continue
            fixture=next(r for r in rows if r['kind']=='fixture'); f=fixture['payload']
            kickoff=datetime.fromisoformat(timestamp(f['kickoff'])); day=kickoff.astimezone(ZoneInfo('Europe/London')).date().isoformat()
            result=by_key.get((f['home_team'],f['away_team'],day))
            if not result or kickoff<=datetime.fromisoformat(snapshot): continue
            books=defaultdict(dict)
            for r in rows:
                if r['kind']=='odds': books[r['payload']['bookmaker']][r['payload']['selection']]=r
            books={b:s for b,s in books.items() if set(s)==set(SIDES)}
            if len(books)<2: continue
            market=dict.fromkeys(SIDES,0.)
            for quotes in books.values():
                raw={k:1/quotes[k]['payload']['decimal_odds'] for k in SIDES}; total=sum(raw.values())
                for k in SIDES: market[k]+=raw[k]/total/len(books)
            predictions=[model.forecast(f['home_team'],f['away_team'],snapdate.isoformat()) for model in models]
            members=[temperature(p['probabilities'],t) for p,t in zip(predictions,report['calibration_temperatures'])]
            weights=report['ensemble_weights']; candidate={k:sum(w*p[k] for w,p in zip(weights,members)) for k in SIDES}
            best={k:max(q[k]['payload']['decimal_odds'] for q in books.values()) for k in SIDES}
            depth=min(predictions[0]['home_history'],predictions[0]['away_history'])
            proposal=residual_proposal(market,members,weights,depth,best)
            oldest=min(r['effective_at'] for q in books.values() for r in q.values())
            from .compare import outcome
            collected[mid]={'match_id':mid,'day':day,'outcome':outcome(result),'snapshot':snapshot,'kickoff':kickoff.isoformat(),
                            'horizon_hours':(kickoff-datetime.fromisoformat(snapshot)).total_seconds()/3600,
                            'maximum_quote_update_age_hours':(datetime.fromisoformat(snapshot)-datetime.fromisoformat(oldest)).total_seconds()/3600,
                            'candidate':candidate,'market':market,'residual_proposal':proposal['probabilities'],'venue':venue.forecast(result),
                            'training_matches':len(training),'team_depth':depth,'archive':digest(envelope)}
            if len(collected)>=target: break
        print(json.dumps({'snapshot':i+1,'matched_fixtures':len(collected),'new_calls':calls,'quota':envelope['quota']}),flush=True)
        if len(collected)>=target: break
    rows=list(collected.values())
    if not rows: raise ValueError('No valid matched fixtures; no performance estimate')
    common=[r for r in rows if r['venue']]
    result={'registered_comparison_hash':digest(report),'experiment_id':'retrospective-market-study-v1','created_at':now(),'matched_fixtures':len(rows),'new_api_calls':calls,'accounted_research_credits':json.loads(budget_path.read_text()),
            'all_matches':{k:score(rows,k) for k in ('candidate','market','residual_proposal')},
            'common_venue_matches':{k:score(common,k) for k in ('candidate','market','residual_proposal','venue')},
            'candidate_vs_market':block_interval(rows,'candidate','market'),
            'proposal_vs_market':block_interval(rows,'residual_proposal','market'),
            'horizon_hours_range':[min(r['horizon_hours'] for r in rows),max(r['horizon_hours'] for r in rows)],
            'maximum_price_update_age_hours':max(r['maximum_quote_update_age_hours'] for r in rows),
            'limitations':['Corrected results hypothetical availability at least3days; original publication unknown.',
                          'First available weekly prices, varying horizons, potentially stale quote updates.',
                          'Exploratory inspected seasons, not untouched lockbox or verified PIT.',
                          'No ROI, execution, novelty or profit claim.'],'predictions':rows}
    archive(directory/'reports',result)
    atomic_json(directory/'market-study.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='predictions'}))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/research/dynamic-v1'); p.add_argument('--target',type=int,default=100); p.add_argument('--max-requests',type=int,default=20); args=p.parse_args()
    run(args.directory,args.target,args.max_requests)
