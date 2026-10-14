"""CC0 OpenFootball results, available only when actually received."""
import argparse
import fcntl
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from .store import Store,timestamp,digest,now
from .provider import archive,load_archive,atomic_json

REVISION='e6744429ee395bc86f247348c6184bb08d4eb361'
SEASONS=('2024-25','2025-26','2026-27')
BASE='https://raw.githubusercontent.com/openfootball/football.json/'
ALIASES={'AFC Bournemouth':'Bournemouth','Brighton & Hove Albion FC':'Brighton and Hove Albion',
         'Sunderland AFC':'Sunderland','Hull City AFC':'Hull City'}


def team(name):
    return ALIASES.get(name,re.sub(r' FC$','',name))


def convert_bootstrap(envelope,existing):
    received=timestamp(envelope['received_at']); season=envelope['season']; data=envelope['response']
    if data.get('name')!='English Premier League '+season[:4]+'/'+season[-2:]:
        raise ValueError('unexpected competition/season')
    known={}
    for row in existing:
        if row['kind']=='fixture':
            p=row['payload']; key=(p['home_team'],p['away_team'],datetime.fromisoformat(timestamp(p['kickoff'])).astimezone(ZoneInfo('Europe/London')).date().isoformat())
            known.setdefault(key,set()).add(row['match_id'])
    records=[]; skipped={'unfinished':0,'future':0,'missing_time':0,'conflicting_score':0}; seen=set()
    for match in data['matches']:
        score=match.get('score'); ft=score.get('ft') if isinstance(score,dict) else None
        if ft is None: skipped['unfinished']+=1; continue
        if len(ft)!=2 or any(type(g) is not int or g<0 for g in ft): raise ValueError('invalid bootstrap score')
        date=match['date']; home=team(match['team1']); away=team(match['team2'])
        if not match.get('time'): skipped['missing_time']+=1; continue
        # Source uses local English fixture wall times. Preserve this interpretation.
        local=datetime.fromisoformat(date+'T'+match['time']).replace(tzinfo=ZoneInfo('Europe/London'))
        kickoff=timestamp(local.isoformat())
        # Never treat a same-day/live score as final using an undated historical file.
        if local.date()>=datetime.fromisoformat(received).astimezone(ZoneInfo('Europe/London')).date():
            skipped['future']+=1; continue
        key=(home,away,date)
        if key in seen: raise ValueError('duplicate fixture in source season')
        seen.add(key)
        candidates=known.get(key,set())
        if len(candidates)>1: raise ValueError('ambiguous event mapping')
        mid=next(iter(candidates)) if candidates else 'openfootball:'+digest({'season':season,'home':home,'away':away,'date':date})
        provider_results=[r for r in existing if r['match_id']==mid and r['kind']=='result' and r['source']=='the-odds-api']
        if provider_results:
            latest=max(provider_results,key=lambda r:(r['available_at'],r['effective_at'],digest(r)))
            if [latest['payload']['home_goals'],latest['payload']['away_goals']]!=ft:
                skipped['conflicting_score']+=1; continue
        base={'match_id':mid,'source':'openfootball','source_ref':digest(envelope),
              'effective_at':received,'available_at':received,'observed_at':received,'ingested_at':received,'availability_basis':'observed_only'}
        # Reuse provider kickoff/name metadata for a mapped fixture, preserving audited IDs.
        prior=max((r for r in existing if r['kind']=='fixture' and r['match_id']==mid),key=lambda r:(r['available_at'],r['effective_at'],digest(r)),default=None)
        payload=dict(prior['payload']) if prior else {'competition_id':'soccer_epl','season':season,'kickoff':kickoff,
            'home_team':home,'away_team':away,'kickoff_timezone_basis':'Europe/London interpretation of source wall time'}
        records.append(dict(base,kind='fixture',key='fixture',payload=payload))
        records.append(dict(base,kind='result',key='result',payload={'home_goals':ft[0],'away_goals':ft[1],'status':'finished',
            'season':season,'original_date':date,'source_time':match['time'],'licence':'CC0-1.0','source_revision':envelope['revision']}))
    return records,skipped


def download(revision,path):
    try:
        with urllib.request.urlopen(BASE+revision+'/'+path,timeout=30) as response: return response.read()
    except (urllib.error.URLError,OSError): raise ValueError('public source download failed') from None


def run(directory='data/prospective',revision=REVISION):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    if not re.fullmatch('[0-9a-f]{40}',revision): raise ValueError('invalid source revision')
    licence=download(revision,'LICENSE.md').decode()
    if 'CC0 1.0 Universal' not in licence: raise ValueError('source licence changed; review needed')
    cache=directory/'bootstrap-archives'; cache.mkdir(exist_ok=True)
    # Cache one immutable pinned revision per season, including the licence snapshot.
    envelopes=[]
    for season in SEASONS:
        pointer=cache/(season+'-'+revision+'.pointer')
        legacy=cache/(season+'.pointer')
        if not pointer.exists() and legacy.exists():
            candidate=load_archive(cache/(legacy.read_text().strip()+'.json'))
            if candidate['revision']==revision: pointer.write_text(legacy.read_text())
        if pointer.exists(): envelope=load_archive(cache/(pointer.read_text().strip()+'.json'))
        else:
            raw=download(revision,season+'/en.1.json')
            envelope={'received_at':now(),'source':'openfootball','revision':revision,'season':season,
                      'source_url':BASE+revision+'/'+season+'/en.1.json','licence':licence,'response':json.loads(raw)}
            sha=archive(cache,envelope); pointer.write_text(sha+'\n')
        envelopes.append(envelope)
    with (directory/'collector.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('collector busy; retry bootstrap shortly') from None
        status_path=directory/'status.json'
        if not status_path.exists(): raise ValueError('collect odds first in the same directory')
        status=json.loads(status_path.read_text()); version=status['dataset_version']; store=Store(directory/'edge.sqlite')
        try:
            reports=[]
            for envelope in envelopes:
                records,skipped=convert_bootstrap(envelope,store.records(version))
                version=store.ingest(records,version)
                reports.append({'season':envelope['season'],'completed_results':len(records)//2,'skipped':skipped})
            status['dataset_version']=version; atomic_json(status_path,status)
            report={'source':'openfootball','licence':'CC0-1.0','revision':revision,'dataset_version':version,
                    'seasons':reports,'availability':'actual cached receipt only; no historical backdating',
                    'warning':'community results, partial recent coverage; no shots/xG or verified historical publication'}
            atomic_json(directory/'bootstrap-report.json',report)
            return report
        finally: store.close()


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/prospective'); args=p.parse_args()
    try: print(json.dumps(run(args.directory)))
    except ValueError as error: print('Bootstrap failed: '+str(error)); raise SystemExit(1)


if __name__=='__main__': main()
