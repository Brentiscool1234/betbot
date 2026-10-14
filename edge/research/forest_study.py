"""Optional sklearn research dependency; never imported by production tracker."""
import argparse,json
from pathlib import Path
from itertools import groupby,product
from .elo_study import load,metrics
from .dynamic import temperature
from ..elo import Elo
from ..form import Form

FEATURE_NAMES=['elo_home','elo_draw','elo_away','elo_rating_difference']+[f'{side}_{window}_{stat}' for window in (5,10) for side in ('home','away') for stat in ('count','points','goals_for','goals_against')]

def features(rows,config):
    elo=Elo(**{k:config[k] for k in ('k','home_advantage','draw_parameter')});form=Form();output=[]
    for day,group in groupby(rows,key=lambda r:r['day']):
        batch=list(group)
        for r in batch:
            e=elo.forecast(r['home'],r['away']);x=list(e['probabilities'].values())+[e['home_rating']-e['away_rating']]+form.features(r['home'],r['away'])
            output.append(dict(r,x=x,elo=e['probabilities']))
        for r in batch:
            elo.observe(r['home'],r['away'],r['hg'],r['ag']);form.observe(r['home'],r['away'],r['hg'],r['ag'])
    return output

def score(model,rows,t):
    probabilities=model.predict_proba([r['x'] for r in rows]);return [dict(r,forest=temperature(dict(zip(model.classes_,p)),t)) for r,p in zip(rows,probabilities)]

def run(paths):
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    config=json.loads(Path(__file__).parents[1].joinpath('elo_config.json').read_text());rows,hashes=load(paths);rows=features(rows,config)
    train=[r for r in rows if r['day']<'2024-06-01'];val=[r for r in rows if '2024-08-01'<=r['day']<'2025-06-01'];test=[r for r in rows if r['day']>='2025-08-01']
    if [len(train),len(val),len(test)]!=[380,380,380]:raise ValueError('three complete E0 seasons required')
    attempts=[]
    for depth in (3,6):
        model=RandomForestClassifier(n_estimators=200,max_depth=depth,min_samples_leaf=20,random_state=20261014,n_jobs=1)
        model.fit([r['x'] for r in train],[r['outcome'] for r in train])
        for t in (.8,1,1.2):attempts.append((metrics(score(model,val,t),'forest')['log_loss'],depth,t))
    loss,depth,t=min(attempts);model=RandomForestClassifier(n_estimators=200,max_depth=depth,min_samples_leaf=20,random_state=20261014,n_jobs=1)
    model.fit([r['x'] for r in train+val],[r['outcome'] for r in train+val]);scored=score(model,test,t)
    return {'status':'retrospective exploratory audit, previously inspected outcomes','source_hashes':hashes,'sklearn_version':sklearn.__version__,'selected_depth':depth,'temperature':t,'validation_log_loss':loss,'test':{key:metrics(scored,key) for key in ('forest','elo','market')},'features':FEATURE_NAMES,'attempts':attempts,'publication':'assumed calendar ordering, not verified PIT'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('files',nargs='+');args=parser.parse_args();print(json.dumps(run(args.files),indent=2))
if __name__=='__main__':main()
