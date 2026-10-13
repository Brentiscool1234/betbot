"""Terminal match tracker with immutable experimental paper decisions/settlement."""
import argparse
import hashlib
import fcntl
import json
import math
import sqlite3
import time
from datetime import datetime,timezone
from pathlib import Path
from .store import Store,canonical,digest,timestamp,now
from .provider import atomic_json
from .poisson import predict,states_at

def code_hash():
    return digest({name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('tracker.py','poisson.py','store.py')})


POLICY={'version':'paper-rule-v1','minimum_model_ev':0.05,'minimum_edge':0.03,
        'maximum_odds_age_seconds':5400,'minimum_bookmakers':2,'prediction_window_hours':24,
        'stake_units':1,'mode':'paper','validation_status':'unvalidated'}


def market(rows,as_of):
    cutoff=datetime.fromisoformat(timestamp(as_of)); groups={}
    for r in rows:
        if r['kind']!='odds': continue
        if max(r['available_at'],r['effective_at'],r['observed_at'])>timestamp(as_of): continue
        age=(cutoff-datetime.fromisoformat(r['effective_at'])).total_seconds()
        if age<0 or age>POLICY['maximum_odds_age_seconds']: continue
        p=r['payload']; groups.setdefault(p['bookmaker'],{})[p['selection']]=r
    books={b:s for b,s in groups.items() if set(s)=={'home','draw','away'}}
    if len(books)<POLICY['minimum_bookmakers']: return {'status':'unavailable','reason':'need two fresh complete bookmaker quotes','bookmakers':len(books)}
    consensus={k:0.0 for k in ('home','draw','away')}
    for selections in books.values():
        raw={k:1/r['payload']['decimal_odds'] for k,r in selections.items()}; total=sum(raw.values())
        for k in consensus: consensus[k]+=raw[k]/total/len(books)
    best={}
    for selection in consensus:
        book,row=max(((b,s[selection]) for b,s in books.items()),key=lambda item:(item[1]['payload']['decimal_odds'],item[0]))
        best[selection]={'bookmaker':book,'decimal_odds':row['payload']['decimal_odds'],
                         'odds_timestamp':row['effective_at'],'source_record':digest(row)}
    return {'status':'available','vig_method':'proportional-v1','consensus':consensus,'best_prices':best,
            'bookmakers':len(books),'source_records':sorted(digest(r) for s in books.values() for r in s.values())}


def suggestion(model,prices):
    if model['status']!='experimental_prediction': return {'status':'insufficient_data','reason':model.get('reason')}
    if prices['status']!='available': return {'status':'no_paper_bet','reason':prices['reason']}
    candidates=[]
    for selection,p in model['probabilities'].items():
        quote=prices['best_prices'][selection]; ev=p*quote['decimal_odds']-1; edge=p-prices['consensus'][selection]
        if ev>=POLICY['minimum_model_ev'] and edge>=POLICY['minimum_edge']:
            candidates.append({'selection':selection,'model_probability':p,'market_probability':prices['consensus'][selection],
                               'model_estimated_ev':ev,'edge':edge,**quote})
    if not candidates: return {'status':'no_paper_bet','reason':'no selection meets the frozen experimental thresholds'}
    best=max(candidates,key=lambda c:(c['model_estimated_ev'],c['selection']))
    return {'status':'experimental_paper_candidate','stake_units':1,'reason':'unvalidated model; paper simulation only',**best}


class PaperLog:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.executescript('''CREATE TABLE IF NOT EXISTS predictions(id TEXT PRIMARY KEY,match_id TEXT UNIQUE NOT NULL,body TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS settlements(prediction TEXT PRIMARY KEY REFERENCES predictions(id),body TEXT NOT NULL);
          PRAGMA foreign_keys=ON;''')
        for table in ('predictions','settlements'):
            for op in ('UPDATE','DELETE'):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS freeze_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'immutable paper record'); END")
    def close(self): self.db.close()
    def freeze(self,body):
        mid=body['match_id']; existing=self.db.execute('SELECT body FROM predictions WHERE match_id=?',(mid,)).fetchone()
        if existing: return json.loads(existing[0])
        body=dict(body,prediction_id=digest(body))
        with self.db: self.db.execute('INSERT INTO predictions VALUES (?,?,?)',(body['prediction_id'],mid,canonical(body)))
        return body
    def settle(self,states,as_of):
        for pid,mid,body in self.db.execute('SELECT id,match_id,body FROM predictions WHERE id NOT IN (SELECT prediction FROM settlements)').fetchall():
            result=next((r for r in states.get(mid,[]) if r['kind']=='result'),None)
            if not result: continue
            if max(result['available_at'],result['effective_at'],result['observed_at'])>timestamp(as_of): continue
            prediction=json.loads(body)
            if timestamp(result['available_at'])<=prediction['prediction_timestamp']: continue
            hg=result['payload']['home_goals']; ag=result['payload']['away_goals']; outcome='home' if hg>ag else 'away' if hg<ag else 'draw'
            current_fixture=next((r for r in states.get(mid,[]) if r['kind']=='fixture'),None)
            rescheduled=bool(current_fixture and timestamp(current_fixture['payload']['kickoff'])!=timestamp(prediction['fixture']['kickoff']))
            probabilities=prediction['model']['probabilities']; pick=prediction['suggestion']
            pnl=pick['decimal_odds']-1 if pick.get('selection')==outcome else -1 if pick.get('selection') else 0
            if rescheduled: pnl=0
            consensus=prediction['market']['consensus']
            market_brier=sum((p-(1 if k==outcome else 0))**2 for k,p in consensus.items())
            market_log_loss=-math.log(max(consensus[outcome],1e-15))
            settlement={'market_brier':market_brier,'market_log_loss':market_log_loss,'void_rescheduled':rescheduled,'prediction_id':pid,'settled_at':timestamp(as_of),'result_record':digest(result),'outcome':outcome,
                        'paper_profit_units':pnl,'brier':sum((p-(1 if k==outcome else 0))**2 for k,p in probabilities.items()),
                        'log_loss':-math.log(max(probabilities[outcome],1e-15))}
            with self.db: self.db.execute('INSERT OR IGNORE INTO settlements VALUES (?,?)',(pid,canonical(settlement)))
    def summary(self):
        settlements=[json.loads(row[0]) for row in self.db.execute('SELECT body FROM settlements')]
        valid=[s for s in settlements if not s.get('void_rescheduled')]
        picks=self.db.execute("SELECT body FROM predictions").fetchall()
        candidate_ids={json.loads(row[0])['prediction_id'] for row in picks if json.loads(row[0])['suggestion'].get('selection')}
        settled_bets=sum(s['prediction_id'] in candidate_ids for s in valid)
        return {'settled_predictions':len(valid),'void_predictions':len(settlements)-len(valid),'settled_paper_bets':settled_bets,'paper_roi':sum(s['paper_profit_units'] for s in valid)/settled_bets if settled_bets else None,'paper_profit_units':sum(s['paper_profit_units'] for s in settlements),
                'mean_brier':sum(s['brier'] for s in valid)/len(valid) if valid else None,
                'mean_market_brier':sum(s['market_brier'] for s in valid)/len(valid) if valid else None,
                'mean_market_log_loss':sum(s['market_log_loss'] for s in valid)/len(valid) if valid else None,
                'mean_model_minus_market_brier':sum(s['brier']-s['market_brier'] for s in valid)/len(valid) if valid else None,
                'mean_log_loss':sum(s['log_loss'] for s in valid)/len(valid) if valid else None,
                'warning':'experimental paper results; no evidence of profitability'}


def scan(directory='data/prospective',current=None):
    directory=Path(directory); current=current or datetime.now(timezone.utc); as_of=timestamp(current.isoformat())
    if not (directory/'status.json').exists(): return {'status':'waiting_for_collection','matches':[]}
    with (directory/'tracker.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return {'status':'locked','matches':[]}
        status=json.loads((directory/'status.json').read_text()); version=status['dataset_version']
        store=Store(directory/'edge.sqlite'); paper=PaperLog(directory/'paper.sqlite')
        try:
            states=states_at(store.records(version),as_of); output=[]
            paper.settle(states,as_of)
            for mid,rows in states.items():
                fixture=next((r for r in rows if r['kind']=='fixture'),None)
                if not fixture: continue
                f=fixture['payload']; kickoff=timestamp(f['kickoff'])
                if kickoff<=as_of: continue
                if any(r['kind']=='result' for r in rows): continue
                model=predict(states,mid,as_of); prices=market(rows,as_of); pick=suggestion(model,prices)
                body={'match_id':mid,'fixture':f,'prediction_timestamp':as_of,'dataset_version':version,
                      'tracker_version':'tracker-v1','code_hash':code_hash(),'policy':POLICY,'policy_hash':digest(POLICY),
                      'model':model,'market':prices,'suggestion':pick}
                hours=(datetime.fromisoformat(kickoff)-current).total_seconds()/3600
                if hours>POLICY['prediction_window_hours'] and model['status']=='experimental_prediction':
                    body['suggestion']={'status':'no_paper_bet','reason':'outside the 24-hour paper decision window'}
                if hours<=POLICY['prediction_window_hours'] and model['status']=='experimental_prediction' and prices['status']=='available':
                    frozen=paper.freeze(body)
                    # Present the actual frozen decision/quote, never masquerade it as current.
                    body=frozen; body['display_note']='frozen paper decision; verify current price separately'
                output.append(body)
            output.sort(key=lambda b:(b['fixture']['kickoff'],b['match_id']))
            from .coverage import diagnose
            coverage=diagnose(states,output,as_of)
            atomic_json(directory/'coverage.json',coverage)
            report={'coverage':coverage,'status':'experimental_paper_tracker','as_of':as_of,'dataset_version':version,'matches':output,'summary':paper.summary()}
            atomic_json(directory/'tracker.json',report)
            return report
        finally: store.close(); paper.close()


def render(report):
    lines=['EDGE — EXPERIMENTAL PAPER TRACKER', 'No real-money instructions; probability model and signal thresholds unvalidated.']
    for row in report['matches']:
        f=row['fixture']; model=row['model']; pick=row['suggestion']
        lines.append(f"\n{f['home_team']} vs {f['away_team']} | kickoff {f['kickoff']}")
        if model['status']!='experimental_prediction':
            lines.append('INSUFFICIENT DATA: '+model.get('reason','unknown')+' '+str(model.get('history_counts',{}))); continue
        p=model['probabilities']; lines.append(f"Model H/D/A: {p['home']:.1%} / {p['draw']:.1%} / {p['away']:.1%}")
        if pick['status']=='experimental_paper_candidate':
            outcome={'home':f["home_team"]+' to win','draw':'Draw','away':f["away_team"]+' to win'}[pick['selection']]
            lines.append(f"PAPER BET: {outcome} | Estimated win probability: {pick['model_probability']:.1%} (uncalibrated) | Odds: {pick['decimal_odds']:.2f} at {pick['bookmaker']} | 1 simulated unit")
            lines.append(f"Model-estimated EV: {pick['model_estimated_ev']:.1%}; probability is not confidence of profitability.")
        else: lines.append('NO BET (paper): '+pick.get('reason','unavailable'))
        if 'prediction_id' in row: lines.append('Frozen at '+row['prediction_timestamp']+'; quote is not guaranteed current.')
    lines.append('\n'+json.dumps(report.get('summary',{})))
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/prospective'); p.add_argument('--watch',action='store_true'); p.add_argument('--json',action='store_true'); args=p.parse_args()
    try:
        while True:
            report=scan(args.directory); print(canonical(report) if args.json else render(report),flush=True)
            if not args.watch: break
            time.sleep(60)
    except KeyboardInterrupt: pass


if __name__=='__main__': main()
