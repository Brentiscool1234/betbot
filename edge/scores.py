"""Prospective final scores. Receipt time is availability; never backdate labels."""
import argparse
import fcntl
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .store import Store, timestamp, digest, validate
from .provider import fetch, archive, load_archive, atomic_json
from .budget import Budget


def convert_scores(envelope):
    received=timestamp(envelope['received_at'])
    reference=digest(envelope)
    records=[]
    for event in envelope['response']:
        if event.get('sport_key') != 'soccer_epl':
            raise ValueError('non-EPL score event')
        if event.get('completed') is not True:
            continue  # live scores must never become final labels
        kickoff=timestamp(event['commence_time'])
        updated=timestamp(event.get('last_update') or received)
        if kickoff>updated or updated>received:
            raise ValueError('invalid final-score timestamp ordering')
        scores=event.get('scores')
        if not isinstance(scores,list) or len(scores)!=2:
            raise ValueError('missing completed-event scores')
        names=[s['name'] for s in scores]
        if set(names)!={event['home_team'],event['away_team']}:
            raise ValueError('score/team mismatch')
        goals={}
        for score in scores:
            value=score['score']
            if type(value) is int and value>=0:
                goals[score['name']]=value
            elif isinstance(value,str) and value.isascii() and value.isdigit():
                goals[score['name']]=int(value)
            else:
                raise ValueError('invalid final score')
        base={'match_id':'the-odds-api:'+event['id'],'source':'the-odds-api',
              'source_ref':reference,'available_at':received,'observed_at':received,
              'ingested_at':received,'availability_basis':'observed_only'}
        records.append(dict(base,kind='fixture',key='fixture',effective_at=received,
            payload={'competition_id':'soccer_epl','kickoff':kickoff,
                     'home_team':event['home_team'],'away_team':event['away_team']}))
        records.append(dict(base,kind='result',key='result',effective_at=updated,
            payload={'home_goals':goals[event['home_team']],'away_goals':goals[event['away_team']],
                     'status':'finished','provider_updated_at':event.get('last_update')}))
    return [validate(r) for r in records]


def collect_scores(directory='data/prospective',fetcher=None,current=None,force=False,daily_limit=60,monthly_limit=1500):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    current=current or datetime.now(timezone.utc)
    with (directory/'collector.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return {'status':'locked'}
        odds_path=directory/'status.json'
        if not odds_path.exists():
            return {'status':'waiting_for_odds','reason':'collect odds first to establish the shared dataset'}
        odds=json.loads(odds_path.read_text())
        score_path=directory/'scores-status.json'
        status=json.loads(score_path.read_text()) if score_path.exists() else {}
        if not force and status.get('next_due') and timestamp(current.isoformat())<timestamp(status['next_due']):
            return dict(status,status='not_due')
        store=Store(directory/'edge.sqlite')
        try:
            version=odds['dataset_version']; applied=set(status.get('applied_archives',[]))
            for path in sorted((directory/'score-archives').glob('*.json')):
                if path.stem not in applied:
                    version=store.ingest(convert_scores(load_archive(path)),version); applied.add(path.stem)
            budget=Budget(directory/'budget.json',daily_limit,monthly_limit)
            blocked=budget.reserve(current,cost=2)
            if blocked:
                atomic_json(directory/'scores-budget-status.json',{'status':'paused_budget','reason':blocked,'checked_at':current.isoformat()})
                return dict(status,status='paused_budget',reason=blocked)
            envelope=(fetcher or (lambda:fetch('sports/soccer_epl/scores',{'daysFrom':3,'dateFormat':'iso'})))()
            budget.reconcile(envelope['quota'],reserved=2)
            sha=archive(directory/'score-archives',envelope)
            records=convert_scores(envelope); version=store.ingest(records,version); applied.add(sha)
            received=datetime.fromisoformat(timestamp(envelope['received_at']))
            result={'status':'collected','last_success':received.isoformat(),'next_due':(received+timedelta(hours=6)).isoformat(),
                    'interval_seconds':21600,'dataset_version':version,'quota':envelope['quota'],
                    'completed_events':sum(r['kind']=='result' for r in records),'applied_archives':sorted(applied)}
            # Preserve odds cadence/freshness while advancing common immutable membership.
            odds['dataset_version']=version; odds['quota']=envelope['quota']
            atomic_json(odds_path,odds)
            atomic_json(score_path,result)
            atomic_json(directory/'scores-budget-status.json',{'status':'within_budget','checked_at':received.isoformat()})
            return result
        finally: store.close()


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/prospective'); args=p.parse_args()
    try:
        result=collect_scores(args.directory)
        print(json.dumps({k:v for k,v in result.items() if k!='applied_archives'}))
        if result['status'] in ('paused_budget','waiting_for_odds'): raise SystemExit(1)
    except Exception as error:
        print(json.dumps({'status':'failed','error':str(error) if type(error) is ValueError else type(error).__name__}))
        raise SystemExit(1)


if __name__=='__main__': main()
