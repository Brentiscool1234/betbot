"""Explicit bounded data acquisition from already reviewed sources."""
import fcntl
import json
import threading
from datetime import datetime,timezone
from pathlib import Path
from .provider import atomic_json
from .store import timestamp,now


def latest_openfootball_revision():
    import urllib.request
    import re
    try:
        request=urllib.request.Request('https://api.github.com/repos/openfootball/football.json/commits/master',headers={'User-Agent':'EDGE-research'})
        with urllib.request.urlopen(request,timeout=30) as response: sha=json.load(response)['sha']
        if not re.fullmatch('[0-9a-f]{40}',sha): raise ValueError('invalid source revision')
        return sha
    except Exception: raise ValueError('Could not check public results source; existing archives retained') from None


def acquire(directory,progress):
    from .collect import collect
    from .scores import collect_scores
    from .bootstrap import run as bootstrap
    from .tracker import scan
    outcomes=[]
    tasks=[('Fetching current EPL odds',lambda:collect(directory,force=True,daily_limit=60,monthly_limit=1500)),
           ('Fetching completed EPL results',lambda:collect_scores(directory,force=True,daily_limit=60,monthly_limit=1500)),
           ('Checking latest CC0 result history',lambda:bootstrap(directory,revision=latest_openfootball_revision())),
           ('Recomputing paper tracker',lambda:scan(directory))]
    for label,task in tasks:
        progress(label)
        try:
            result=task(); status=result.get('status','imported')
            outcomes.append({'step':label,'status':status,'reason':result.get('reason'),'completed_events':result.get('completed_events'),
                             'imported_results':sum(s['completed_results'] for s in result.get('seasons',[])) if 'seasons' in result else None})
        except Exception as error:
            outcomes.append({'step':label,'status':'failed','reason':str(error) if type(error) is ValueError else type(error).__name__})
    return outcomes


class RefreshManager:
    def __init__(self,directory,runner=acquire,clock=None):
        self.directory=Path(directory); self.directory.mkdir(parents=True,exist_ok=True)
        self.runner=runner; self.clock=clock or (lambda:datetime.now(timezone.utc)); self.mutex=threading.Lock(); self.thread=None
        previous=self.status()
        if previous.get('status')=='running':
            with (self.directory/'data-refresh.lock').open('a') as lock:
                try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: pass
                else:
                    previous.update(status='failed',stage='Previous refresh was interrupted; existing data retained',finished_at=now())
                    atomic_json(self.directory/'data-refresh.json',previous)
    def status(self):
        path=self.directory/'data-refresh.json'
        return json.loads(path.read_text()) if path.exists() else {'status':'idle'}
    def start(self):
        with self.mutex:
            lock=(self.directory/'data-refresh.lock').open('a')
            try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: lock.close(); return {'status':'busy','reason':'A refresh is already running'},409
            current=self.clock(); previous=self.status()
            if previous.get('started_at'):
                elapsed=(current-datetime.fromisoformat(timestamp(previous['started_at']))).total_seconds()
                if elapsed<300:
                    lock.close(); return {'status':'cooldown','retry_after_seconds':max(1,int(300-elapsed)),'reason':'Data refresh is limited to once every five minutes'},429
            state={'status':'running','started_at':current.isoformat(),'stage':'Starting data refresh',
                   'estimated_provider_credits':3,'warning':'No additional subscription; actual quota headers and budget caps apply'}
            atomic_json(self.directory/'data-refresh.json',state)
            self.thread=threading.Thread(target=self._run,args=(lock,state),daemon=True); self.thread.start()
            return state,202
    def _run(self,lock,state):
        def progress(label):
            state['stage']=label; atomic_json(self.directory/'data-refresh.json',state)
        try:
            outcomes=self.runner(self.directory,progress)
            issues=any(o['status'] in ('failed','paused_budget','locked','waiting_for_odds') for o in outcomes)
            state.update(status='partial' if issues else 'completed',stage='Refresh finished',outcomes=outcomes,finished_at=now())
        except Exception as error:
            state.update(status='failed',stage='Refresh stopped',error=str(error) if type(error) is ValueError else type(error).__name__,finished_at=now())
        finally:
            atomic_json(self.directory/'data-refresh.json',state); lock.close()
