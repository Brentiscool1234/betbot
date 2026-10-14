"""Auditable chronological CSV comparison; historical publication unverified."""
import argparse,csv,json,math,hashlib,random
from datetime import datetime
from itertools import product,groupby
from pathlib import Path
from ..elo import Elo,blend
from .dynamic import Dynamic,temperature

CONFIG=json.loads(Path(__file__).with_name('live_config.json').read_text())

def load(paths):
    rows={}; hashes={}
    for path in paths:
        p=Path(path); hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
        for r in csv.DictReader(p.read_text(encoding='utf-8-sig').splitlines()):
            if not r.get('Date') or not r.get('HomeTeam'): continue
            if r.get('Div')!='E0': raise ValueError('This experiment accepts E0 only; league adjustment not fitted')
            day=datetime.strptime(r['Date'],'%d/%m/%Y').date().isoformat()
            if day>'2026-05-24': continue
            hg=int(r['FTHG']); ag=int(r['FTAG']); outcome='home' if hg>ag else 'away' if hg<ag else 'draw'
            row={'day':day,'home':r['HomeTeam'],'away':r['AwayTeam'],'hg':hg,'ag':ag,'outcome':outcome}
            odds={k:float(r['Avg'+suffix]) for k,suffix in [('home','H'),('draw','D'),('away','A')] if r.get('Avg'+suffix)}
            if len(odds)==3 and min(odds.values())>1:
                total=sum(1/v for v in odds.values());row['market']={k:1/v/total for k,v in odds.items()}
            key=(day,row['home'],row['away'])
            if key in rows and (rows[key]['hg'],rows[key]['ag'])!=(hg,ag): raise ValueError('conflicting duplicate result')
            rows[key]=row
    return sorted(rows.values(),key=lambda r:(r['day'],r['home'],r['away'])),hashes

def forecasts(rows,k,home,draw):
    elo=Elo(k,home,draw); models=[Dynamic(**c) for c in CONFIG['adaptation_configs']]; out=[]
    for day,group in groupby(rows,key=lambda r:r['day']):
        batch=list(group)
        for r in batch:
            members=[temperature(m.forecast(r['home'],r['away'],day)['probabilities'],t) for m,t in zip(models,CONFIG['temperatures'])]
            football={s:sum(w*p[s] for w,p in zip(CONFIG['weights'],members)) for s in ('home','draw','away')}
            out.append(dict(r,football=football,elo=elo.forecast(r['home'],r['away'])['probabilities']))
        # Entire date forecast before learning any result on that date.
        for r in batch:
            elo.observe(r['home'],r['away'],r['hg'],r['ag'])
            for m in models:m.observe(r['home'],r['away'],day,r['hg'],r['ag'])
    return out

def metrics(rows,key):
    eligible=[r for r in rows if key in r]; n=len(eligible)
    return {'matches':n,'accuracy':sum(max(r[key],key=r[key].get)==r['outcome'] for r in eligible)/n,
            'log_loss':sum(-math.log(max(r[key][r['outcome']],1e-15)) for r in eligible)/n,
            'brier':sum(sum((p-(s==r['outcome']))**2 for s,p in r[key].items()) for r in eligible)/n}

def run(paths):
    rows,hashes=load(paths)
    candidates=[]
    for k,h,d in product((20,40),(50,80),(.55,.75,1)):
        predicted=forecasts(rows,k,h,d)
        validation=[r for r in predicted if '2024-08-01'<=r['day']<'2025-06-01']
        if len(validation)!=380:raise ValueError('need complete 2024/25 validation season')
        for weight in (0,.25,.5,1):
            scored=[dict(r,candidate=blend(r['football'],r['elo'],weight)) for r in validation]
            candidates.append((metrics(scored,'candidate')['log_loss'],k,h,d,weight))
    loss,k,h,d,weight=min(candidates)
    selected={'k':k,'home_advantage':h,'draw_parameter':d,'blend_weight':weight}
    test=[dict(r,candidate=blend(r['football'],r['elo'],weight)) for r in forecasts(rows,k,h,d) if '2025-08-01'<=r['day']<'2026-06-01']
    if len(test)!=380:raise ValueError('need complete 2025/26 audit season')
    days=[list(g) for _,g in groupby(test,key=lambda r:r['day'])];rng=random.Random(20261014);diff=[]
    for _ in range(1000):
        sample=[]
        while len(sample)<len(days):
            start=rng.randrange(len(days)); sample.extend(days[(start+j)%len(days)] for j in range(5))
        sampled=[r for g in sample[:len(days)] for r in g]
        diff.append(metrics(sampled,'candidate')['log_loss']-metrics(sampled,'football')['log_loss'])
    diff.sort()
    return {'status':'retrospective audit, previously inspected outcomes; prospective reliability unverified','source_hashes':hashes,'config':selected,'validation_log_loss':loss,'test':{key:metrics(test,key) for key in ('candidate','football','elo','market')},'candidate_minus_football_logloss_approx95_interval':[diff[25],diff[974]],'historical_publication':'assumed by calendar ordering; exact availability not verified','rank_scope':'Premier League only; lower-division strength not calibrated','grid_attempts':len(candidates)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('files',nargs='+');args=parser.parse_args();print(json.dumps(run(args.files),indent=2))
if __name__=='__main__':main()
