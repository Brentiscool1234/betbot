"""Fixed 2024 weekly historical sampling plan with resumable cached responses."""
import argparse
import fcntl
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .store import Store
from .provider import fetch, archive, load_archive, convert, atomic_json
from .quality import report


def _run(directory, target=100, max_requests=20):
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    store = Store(directory/'edge.sqlite')
    version = None
    try:
        cached_dates={}
        for path in sorted((directory/'archives').glob('*.json')):
            envelope=load_archive(path)
            version = store.ingest(convert(envelope,historical=True),version)
            cached_dates[envelope['request']['parameters']['date']]=path.stem
        for i in range(max_requests):
            quality = report(store,version) if version else None
            if quality and quality['t24_demonstrations'] >= target:
                break
            date = (datetime(2024,8,8,12,tzinfo=timezone.utc)+timedelta(days=7*i)).strftime('%Y-%m-%dT%H:%M:%SZ')
            index = directory/f'snapshot-{i:02d}.json'
            if date in cached_dates:
                atomic_json(index,{'archive':cached_dates[date]})
                continue
            envelope = fetch('historical/sports/soccer_epl/odds',{'regions':'uk','markets':'h2h','oddsFormat':'decimal','date':date})
            sha = archive(directory/'archives',envelope)
            version = store.ingest(convert(envelope,historical=True),version)
            atomic_json(index,{'archive':sha})
            quality = report(store,version)
            print(json.dumps({'snapshot':i+1,'t24_demonstrations':quality['t24_demonstrations'],'quota':envelope['quota']}),flush=True)
        if not version:
            raise ValueError('no historical data')
        quality = report(store,version)
        atomic_json(directory/'quality.json',quality)
        atomic_json(directory/'status.json',{'dataset_version':version,'completed_at':datetime.now(timezone.utc).isoformat()})
        if quality['t24_demonstrations'] < target:
            raise ValueError('historical target not met; bounded sampling stopped')
        return quality
    finally:
        store.close()


def run(directory,target=100,max_requests=20):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    with (directory/'historical.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('historical collection already running') from None
        return _run(directory,target,max_requests)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/historical'); p.add_argument('--target',type=int,default=100); p.add_argument('--max-requests',type=int,default=20)
    args=p.parse_args()
    try:
        result=run(args.directory,args.target,args.max_requests)
        print(json.dumps({k:v for k,v in result.items() if k!='demonstrations'}))
    except (ValueError,KeyError,TypeError,OSError) as error:
        # Provider errors are sanitized in fetch. Never print arbitrary transport exception URLs.
        print('Historical collection failed: '+str(error) if isinstance(error,ValueError) else 'Historical collection failed: '+type(error).__name__)
        raise SystemExit(1)


if __name__=='__main__': main()
