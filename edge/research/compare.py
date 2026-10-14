"""Retrospective chronological method study, NOT point-in-time betting evidence."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
from .dynamic import Dynamic,temperature,SIDES
from ..poisson import probabilities
from ..store import canonical,digest,now
from ..provider import atomic_json,archive

CONFIGS=[{'learning_rate':.01,'half_life':365},{'learning_rate':.03,'half_life':180},{'learning_rate':.06,'half_life':90}]
TEMPERATURES=(.8,1.,1.2,1.4)


def loss(p,y): return -math.log(max(p[y],1e-15))
def brier(p,y): return sum((p[k]-(k==y))**2 for k in SIDES)
def outcome(m): return 'home' if m['hg']>m['ag'] else 'away' if m['hg']<m['ag'] else 'draw'


def load(directory):
    from ..bootstrap import REVISION,download,team
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True); matches=[]; hashes={}
    for season in ('2024-25','2025-26'):
        path=directory/(season+'.json')
        if not path.exists(): path.write_bytes(download(REVISION,season+'/en.1.json'))
        raw=path.read_bytes(); hashes[season]=hashlib.sha256(raw).hexdigest(); data=json.loads(raw)
        if data['name']!='English Premier League '+season[:4]+'/'+season[-2:]: raise ValueError('unexpected season')
        seen=set()
        for m in data['matches']:
            score=m.get('score'); ft=score.get('ft') if isinstance(score,dict) else None
            if not ft: continue
            if len(ft)!=2 or any(type(g) is not int or g<0 for g in ft): raise ValueError('invalid goals')
            key=(m['date'],team(m['team1']),team(m['team2']))
            if key in seen: raise ValueError('duplicate match')
            seen.add(key); matches.append({'day':key[0],'home':key[1],'away':key[2],'hg':ft[0],'ag':ft[1],'season':season})
    return sorted(matches,key=lambda m:(m['day'],m['home'],m['away'])),hashes


class Venue:
    def __init__(self): self.history=[]
    def forecast(self,m):
        if len(self.history)<50: return None
        h=[x for x in self.history if x['home']==m['home']][-20:]; a=[x for x in self.history if x['away']==m['away']][-20:]
        if min(len(h),len(a))<5: return None
        lh=sum(x['hg'] for x in self.history)/len(self.history); la=sum(x['ag'] for x in self.history)/len(self.history)
        home=(sum(x['hg'] for x in h)+5*lh)/(len(h)+5)*(sum(x['hg'] for x in a)+5*lh)/(len(a)+5)/lh
        away=(sum(x['ag'] for x in a)+5*la)/(len(a)+5)*(sum(x['ag'] for x in h)+5*la)/(len(h)+5)/la
        return probabilities(home,away)


def score(rows,key):
    rows=[r for r in rows if r.get(key)]
    if not rows: return {'n':0}
    ece=0
    for j in range(10):
        bucket=[r for r in rows if min(9,int(max(r[key].values())*10))==j]
        if bucket:
            conf=sum(max(r[key].values()) for r in bucket)/len(bucket)
            accuracy=sum(max(r[key],key=r[key].get)==r['outcome'] for r in bucket)/len(bucket)
            ece+=len(bucket)/len(rows)*abs(conf-accuracy)
    return {'n':len(rows),'log_loss':sum(loss(r[key],r['outcome']) for r in rows)/len(rows),
            'brier':sum(brier(r[key],r['outcome']) for r in rows)/len(rows),'top_label_ece_10bins':ece}


def block_interval(rows,a,b):
    groups=defaultdict(list)
    for r in rows:
        if r.get(a) and r.get(b): groups[r['day']].append(loss(r[a],r['outcome'])-loss(r[b],r['outcome']))
    days=sorted(groups); rng=random.Random(20261014); estimates=[]
    for _ in range(500):
        selected=[]
        while len(selected)<len(days):
            start=rng.randrange(len(days)); selected.extend(days[(start+k)%len(days)] for k in range(5))
        values=[v for day in selected[:len(days)] for v in groups[day]]
        estimates.append(sum(values)/len(values))
    estimates.sort(); return {'candidate_minus_baseline_log_loss_ci95':[estimates[12],estimates[487]],'block_unit':'5 consecutive match dates','resamples':500,'paired_matches':sum(map(len,groups.values()))}


def compare(matches):
    first=[m for m in matches if m['season']=='2024-25']; cutoff=first[199]['day']
    models=[Dynamic(**config) for config in CONFIGS]; venue=Venue(); groups=defaultdict(list)
    for m in matches: groups[m['day']].append(m)
    validation=[]; test=[]
    for day,day_matches in sorted(groups.items()):
        # Forecast entire date before any result on that date is observed.
        forecast=[]
        for m in day_matches:
            ps=[model.forecast(m['home'],m['away'],day)['probabilities'] for model in models]
            past=venue.history
            base=probabilities(sum(x['hg'] for x in past)/len(past),sum(x['ag'] for x in past)/len(past)) if past else probabilities(1.5,1.2)
            forecast.append({'day':day,'outcome':outcome(m),'members':ps,'venue':venue.forecast(m),'league':base})
        if day>cutoff:
            (validation if day_matches[0]['season']=='2024-25' else test).extend(forecast)
        for m in day_matches:
            for model in models: model.observe(m['home'],m['away'],day,m['hg'],m['ag'])
            venue.history.append(m)
    trials=[]; temps=[]; weights=[]
    for i,config in enumerate(CONFIGS):
        choices=[]
        for temp in TEMPERATURES:
            rows=[dict(r,p=temperature(r['members'][i],temp)) for r in validation]
            metric=score(rows,'p'); trials.append({'config':config,'temperature':temp,'validation':metric}); choices.append((metric['log_loss'],temp))
        best,temp=min(choices); temps.append(temp); weights.append(math.exp(-best))
    weights=[w/sum(weights) for w in weights]
    for row in test:
        members=[temperature(p,t) for p,t in zip(row['members'],temps)]
        row['candidate']={k:sum(w*p[k] for w,p in zip(weights,members)) for k in SIDES}
    common=[r for r in test if r['venue']]
    return {'training_cutoff':cutoff,'initial_training_matches':sum(m['day']<=cutoff for m in matches),
            'validation_matches':len(validation),'test_matches':len(test),'calibration_temperatures':temps,'ensemble_weights':weights,
            'all_validation_attempts':trials,'all_test_matches':{'candidate':score(test,'candidate'),'league_baseline':score(test,'league')},
            'matched_venue_subset':{'candidate':score(common,'candidate'),'current_venue_baseline':score(common,'venue'),
                                    'paired_block_uncertainty':block_interval(common,'candidate','venue')},
            'test_predictions':test,'market_comparison':'NOT AVAILABLE for held-out season; no market-edge claim',
            'deployment_decision':'research only; no automatic active model replacement'}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/research/dynamic-v1'); args=p.parse_args()
    matches,hashes=load(args.directory); result=compare(matches)
    result.update(code_hash=digest({name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('compare.py','dynamic.py')}),experiment_id='dynamic-opponent-research-v1',created_at=now(),source_hashes=hashes,data_version=digest(hashes),
      limitations=['Retrospective latest corrected results, observed in2026; publication times unknown.',
                   'Event-ordered forecasts do not establish verified historical point-in-time availability.',
                   'Partial2025/26 coverage; not an untouched lockbox.','Calibration selected on limited validation sample.',
                   'No odds, execution, CLV, ROI or profitability evidence.','Original implementation combines established methods; uniqueness not verified.'])
    archive(Path(args.directory)/'reports',result)
    atomic_json(Path(args.directory)/'report.json',result)
    print(canonical({k:v for k,v in result.items() if k not in ('test_predictions','all_validation_attempts')}))


if __name__=='__main__': main()
