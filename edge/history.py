"""Automatic reviewed-source history upkeep, not unrestricted scraping."""
import argparse
import fcntl
from pathlib import Path
from datetime import datetime,timezone
from .provider import atomic_json
from .store import now


def _update(directory='data/prospective',revision_fetcher=None,importer=None,scanner=None):
    from .refresh import latest_openfootball_revision
    from .bootstrap import run
    from .tracker import scan
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    atomic_json(directory/'history-enabled.json',{'enabled':True})
    state={'status':'running','started_at':now(),'source':'openfootball'}
    atomic_json(directory/'history-status.json',state)
    try:
        revision=(revision_fetcher or latest_openfootball_revision)()
        result=(importer or run)(directory,revision=revision)
        report=(scanner or scan)(directory)
        if report.get('status')=='locked': raise ValueError('tracker busy; history imported but coverage update pending')
        state.update(status='completed',last_success=now(),revision=revision,completed_results=sum(s['completed_results'] for s in result['seasons']),
                     model_ready=sum(m['model']['status']=='experimental_prediction' for m in report['matches']),upcoming_matches=len(report['matches']))
    except Exception as error:
        state.update(status='failed',error=str(error) if type(error) is ValueError else type(error).__name__)
        previous=directory/'history-last-success.json'
        if previous.exists():
            import json
            state['last_success']=json.loads(previous.read_text()).get('last_success')
    state['finished_at']=now()
    atomic_json(directory/'history-status.json',state)
    if state['status']=='completed': atomic_json(directory/'history-last-success.json',state)
    return state


def update(directory='data/prospective',revision_fetcher=None,importer=None,scanner=None):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    with (directory/'history.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return {'status':'locked','error':'History upkeep already running'}
        return _update(directory,revision_fetcher,importer,scanner)


def main():
    import json
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/prospective'); args=p.parse_args()
    result=update(args.directory); print(json.dumps(result)); raise SystemExit(0 if result['status']=='completed' else 1)


if __name__=='__main__': main()
