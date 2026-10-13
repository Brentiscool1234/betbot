"""Locked adaptive pre-match odds collector; private archives are replayable."""
import argparse
import fcntl
import json
import signal
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .store import Store, timestamp
from .budget import Budget
from .provider import fetch, archive, load_archive, convert, atomic_json


def cadence(events, current, profile='research'):
    upcoming = [(datetime.fromisoformat(timestamp(e['commence_time']))-current).total_seconds() for e in events]
    nearest = min((x for x in upcoming if x>0),default=float('inf'))
    if profile == 'pilot':
        return 3600 if nearest <= 21600 else 21600
    if profile != 'research':
        raise ValueError('unknown cadence profile')
    return 300 if nearest<=3600 else 900 if nearest<=21600 else 3600 if nearest<=86400 else 21600


def collect(directory='data/prospective', fetcher=None, current=None, force=False, daily_limit=20, monthly_limit=400, profile='pilot'):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    current=current or datetime.now(timezone.utc)
    with (directory/'collector.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return {'status':'locked'}
        status_path=directory/'status.json'
        status=json.loads(status_path.read_text()) if status_path.exists() else {}
        if not force and status.get('next_due') and timestamp(current.isoformat()) < timestamp(status['next_due']):
            return dict(status,status='not_due')
        store=Store(directory/'edge.sqlite')
        try:
            version=status.get('dataset_version')
            # Replay archived but uncommitted responses after a crash.
            applied=set(status.get('applied_archives',[]))
            for path in sorted((directory/'archives').glob('*.json')):
                if path.stem not in applied:
                    version=store.ingest(convert(load_archive(path)),version)
                    applied.add(path.stem)
            budget=Budget(directory/'budget.json',daily_limit,monthly_limit)
            blocked=budget.reserve(current)
            if blocked:
                atomic_json(directory/'budget-status.json',{'status':'paused_budget','reason':blocked,'checked_at':current.isoformat()})
                return dict(status,status='paused_budget',reason=blocked)
            envelope=(fetcher or (lambda:fetch('sports/soccer_epl/odds',{'regions':'uk','markets':'h2h','oddsFormat':'decimal'})))()
            budget.reconcile(envelope['quota'])
            atomic_json(directory/'budget-status.json',{'status':'within_budget','checked_at':current.isoformat()})
            sha=archive(directory/'archives',envelope)
            version=store.ingest(convert(envelope),version); applied.add(sha)
            received=datetime.fromisoformat(timestamp(envelope['received_at']))
            interval=cadence(envelope['response'],received,profile)
            result={'status':'collected','last_success':received.isoformat(),'next_due':(received+timedelta(seconds=interval)).isoformat(),
                    'interval_seconds':interval,'dataset_version':version,'quota':envelope['quota'],
                    'events':len(envelope['response']),'applied_archives':sorted(applied)}
            atomic_json(status_path,result)
            return result
        finally: store.close()


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/prospective'); p.add_argument('--watch',action='store_true'); p.add_argument('--force',action='store_true'); p.add_argument('--daily-limit',type=int,default=20); p.add_argument('--monthly-limit',type=int,default=400)
    p.add_argument('--profile',choices=('pilot','research'),default='pilot')
    args=p.parse_args()
    if args.watch and args.force: p.error('--force cannot be combined with --watch')
    stopped=False
    def stop(*_):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    while not stopped:
        try:
            result=collect(args.directory,force=args.force,daily_limit=args.daily_limit,monthly_limit=args.monthly_limit,profile=args.profile)
            if result['status']!='not_due':
                print(json.dumps({k:v for k,v in result.items() if k!='applied_archives'}),flush=True)
            pause=60
        except Exception as error:
            print(json.dumps({'status':'failed','error':str(error) if type(error) is ValueError else type(error).__name__}),flush=True)
            if not args.watch: raise SystemExit(1)
            pause=300
        if not args.watch: break
        deadline=time.monotonic()+pause
        while not stopped and time.monotonic()<deadline: time.sleep(1)


if __name__=='__main__': main()
