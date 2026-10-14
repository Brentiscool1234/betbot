"""Import owner-supplied Football-Data E0 results at actual receipt time."""
import argparse,csv,fcntl,hashlib,json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from .store import Store,now,timestamp,digest
from .provider import atomic_json

ALIASES={'Man City':'Manchester City','Man United':'Manchester United',"Nott'm Forest":'Nottingham Forest','Wolves':'Wolverhampton Wanderers','Brighton':'Brighton and Hove Albion','Tottenham':'Tottenham Hotspur','Newcastle':'Newcastle United','West Ham':'West Ham United','Leeds':'Leeds United','Leicester':'Leicester City','Sheffield United':'Sheffield United','West Brom':'West Bromwich Albion','Ipswich':'Ipswich Town','Hull':'Hull City','Coventry':'Coventry City'}

def convert(raw,received,existing):
    received=timestamp(received);source_hash=hashlib.sha256(raw).hexdigest();records=[];seen=set();skipped={'future_or_same_day':0,'score_conflict':0}
    known={}
    for r in existing:
        if r['kind']=='fixture' and r['payload']['competition_id']=='soccer_epl':
            p=r['payload'];day=datetime.fromisoformat(timestamp(p['kickoff'])).astimezone(ZoneInfo('Europe/London')).date().isoformat()
            known.setdefault((day,p['home_team'],p['away_team']),{})[r['match_id']]=r
    for r in csv.DictReader(raw.decode('utf-8-sig').splitlines()):
        if not r.get('Date') or not r.get('HomeTeam'):continue
        if r.get('Div')!='E0':raise ValueError('E0 Premier League files only; lower-division strength not calibrated')
        day=datetime.strptime(r['Date'],'%d/%m/%Y').date()
        if day>=datetime.fromisoformat(received).astimezone(ZoneInfo('Europe/London')).date():skipped['future_or_same_day']+=1;continue
        home=ALIASES.get(r['HomeTeam'],r['HomeTeam']);away=ALIASES.get(r['AwayTeam'],r['AwayTeam']);key=(day.isoformat(),home,away)
        if key in seen:raise ValueError('duplicate CSV fixture')
        seen.add(key);hg=int(r['FTHG']);ag=int(r['FTAG'])
        if min(hg,ag)<0 or home==away:raise ValueError('invalid CSV result')
        expected='H' if hg>ag else 'A' if hg<ag else 'D'
        if r.get('FTR') and r['FTR']!=expected:raise ValueError('CSV outcome disagrees with goals')
        matches=known.get(key,{})
        if len(matches)>1:raise ValueError('ambiguous existing match mapping')
        prior=next(iter(matches.values()),None);mid=prior['match_id'] if prior else 'football-data:'+digest(key)
        scores=[s['payload'] for s in existing if s['kind']=='result' and s['match_id']==mid]
        if any((s['home_goals'],s['away_goals'])!=(hg,ag) for s in scores):skipped['score_conflict']+=1;continue
        time=r.get('Time') or '12:00'
        kickoff=timestamp(datetime.fromisoformat(day.isoformat()+'T'+time).replace(tzinfo=ZoneInfo('Europe/London')).isoformat())
        season_start=day.year if day.month>=7 else day.year-1;season=f'{season_start}-{str(season_start+1)[-2:]}'
        payload=dict(prior['payload']) if prior else {'home_team':home,'away_team':away,'competition_id':'soccer_epl','season':season,'kickoff':kickoff,'kickoff_timezone_basis':'Europe/London CSV wall time; noon placeholder if time absent'}
        base={'match_id':mid,'source':'football-data-owner-upload','source_ref':source_hash,'effective_at':received,'available_at':received,'observed_at':received,'ingested_at':received,'availability_basis':'observed_only'}
        records.extend([dict(base,kind='fixture',key='fixture',payload=payload),dict(base,kind='result',key='result',payload={'home_goals':hg,'away_goals':ag,'status':'finished','season':season,'original_date':day.isoformat()})])
    return records,skipped

def run(files,directory='data/prospective'):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);cache=directory/'csv-archives';cache.mkdir(exist_ok=True)
    with (directory/'collector.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('collector busy; retry import') from None
        status_path=directory/'status.json'
        if not status_path.exists():raise ValueError('collect odds first')
        status=json.loads(status_path.read_text());version=status['dataset_version'];store=Store(directory/'edge.sqlite');reports=[]
        try:
            for file in files:
                raw=Path(file).read_bytes();sha=hashlib.sha256(raw).hexdigest();receipt=cache/(sha+'.json')
                if not receipt.exists():
                    (cache/(sha+'.csv')).write_bytes(raw);atomic_json(receipt,{'received_at':now(),'source':'https://football-data.co.uk/englandm.php','sha256':sha})
                received=json.loads(receipt.read_text())['received_at'];records,skipped=convert(raw,received,store.records(version));version=store.ingest(records,version)
                reports.append({'file':Path(file).name,'sha256':sha,'completed_results':len(records)//2,'skipped':skipped})
            status['dataset_version']=version;atomic_json(status_path,status)
            report={'dataset_version':version,'files':reports,'availability':'observed on import; no historical backdating'};atomic_json(directory/'csv-report.json',report);return report
        finally:store.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('files',nargs='+');p.add_argument('--directory',default='data/prospective');a=p.parse_args()
    files=[]
    for name in a.files:
        path=Path(name)
        files.extend(sorted(path.glob('E0*.csv')) if path.is_dir() else [path])
    if not files:raise SystemExit('No E0 CSV files found')
    try:print(json.dumps(run(files,a.directory)))
    except (ValueError,OSError) as e:raise SystemExit('CSV import failed: '+str(e))
if __name__=='__main__':main()
