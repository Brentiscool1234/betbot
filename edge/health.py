"""Local service health; exits nonzero on stale data, budget pause or low disk."""
import argparse
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path
from .store import timestamp


def check(directory,current=None):
    directory=Path(directory); current=current or datetime.now(timezone.utc)
    problems=[]
    path=directory/'status.json'
    if not path.exists(): return {'healthy':False,'problems':['no successful collection recorded']}
    status=json.loads(path.read_text())
    age=(current-datetime.fromisoformat(timestamp(status['last_success']))).total_seconds()
    if age<0 or age>status['interval_seconds']+600: problems.append('collection stale or clock incorrect')
    budget=directory/'budget-status.json'
    if budget.exists() and json.loads(budget.read_text()).get('status')=='paused_budget': problems.append('collection paused by budget; coverage incomplete')
    if (directory/'results-enabled.json').exists():
        scores_path=directory/'scores-status.json'
        if not scores_path.exists():
            problems.append('no successful results collection recorded')
        else:
            scores=json.loads(scores_path.read_text())
            scores_age=(current-datetime.fromisoformat(timestamp(scores['last_success']))).total_seconds()
            if scores_age<0 or scores_age>scores['interval_seconds']+600:
                problems.append('results collection stale or clock incorrect')
        scores_budget=directory/'scores-budget-status.json'
        if scores_budget.exists() and json.loads(scores_budget.read_text()).get('status')=='paused_budget':
            problems.append('results collection paused by budget')
    if (directory/'history-enabled.json').exists():
        history_path=directory/'history-status.json'
        history=json.loads(history_path.read_text()) if history_path.exists() else {}
        if history.get('status')=='failed': problems.append('automatic history update failed')
        if not history.get('last_success'): problems.append('no successful automatic history update')
        elif (current-datetime.fromisoformat(timestamp(history['last_success']))).total_seconds()>36*3600:
            problems.append('automatic history update stale')
    if shutil.disk_usage(directory).free<200*1024*1024: problems.append('less than 200 MiB disk available')
    try:
        if int(status.get('quota',{}).get('remaining','1000'))<200: problems.append('provider credits below 200')
    except (TypeError,ValueError): problems.append('provider quota unavailable')
    return {'healthy':not problems,'problems':problems,'last_success':status['last_success'],'age_seconds':round(age),'dataset_version':status['dataset_version']}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/prospective'); args=p.parse_args()
    result=check(args.directory); print(json.dumps(result)); raise SystemExit(0 if result['healthy'] else 1)


if __name__=='__main__': main()
