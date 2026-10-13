import math
import sqlite3
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from edge.poisson import probabilities,predict,states_at
from edge.store import timestamp,validate,digest,Store
from edge.tracker import market,suggestion,PaperLog,POLICY,scan


def observation(mid,kind,payload,available,key=None):
    t=timestamp(available.isoformat())
    return validate({'match_id':mid,'kind':kind,'key':key or kind,'source':'test','source_ref':'synthetic-only',
     'effective_at':t,'available_at':t,'observed_at':t,'ingested_at':t,'availability_basis':'observed_only','payload':payload})


def histories(current,n=60):
    rows=[]
    for i in range(n):
        day=current-timedelta(days=i+2); mid='prior-'+str(i)
        rows.append(observation(mid,'fixture',{'home_team':'A','away_team':'B','competition_id':'soccer_epl','kickoff':day.isoformat()},day-timedelta(hours=24)))
        rows.append(observation(mid,'result',{'home_goals':2,'away_goals':1,'status':'finished'},day+timedelta(hours=3)))
    rows.append(observation('target','fixture',{'home_team':'A','away_team':'B','competition_id':'soccer_epl','kickoff':(current+timedelta(hours=12)).isoformat()},current-timedelta(hours=24)))
    return rows


def odds(current,price=4):
    return [observation('target','odds',{'bookmaker':book,'selection':selection,'decimal_odds':price,'market':'1X2'},current,key=book+':'+selection)
            for book in ('one','two') for selection in ('home','draw','away')]


class PoissonTests(unittest.TestCase):
    def test_distributions_symmetry_normalization_and_strength(self):
        equal=probabilities(1.5,1.5); strong=probabilities(2.5,0.5)
        self.assertAlmostEqual(sum(equal.values()),1); self.assertAlmostEqual(equal['home'],equal['away'])
        self.assertGreater(strong['home'],strong['away'])
        self.assertEqual(probabilities(0,0),{'home':0,'draw':1,'away':0})
        for rate in (-1,float('nan'),101):
            with self.assertRaises(ValueError): probabilities(rate,1)
    def test_no_future_current_or_late_correction_enters_training(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); rows=histories(current)
        baseline=predict(states_at(rows,current.isoformat()),'target',current.isoformat())
        self.assertEqual(baseline['history_counts']['league'],60)
        self.assertAlmostEqual(baseline['lambda_home'],2); self.assertAlmostEqual(baseline['lambda_away'],1)
        late=observation('prior-0','result',{'home_goals':99,'away_goals':0,'status':'finished'},current+timedelta(seconds=1))
        rows.append(late); rows.append(observation('target','result',{'home_goals':99,'away_goals':0,'status':'finished'},current))
        self.assertEqual(baseline,predict(states_at(rows,current.isoformat()),'target',current.isoformat()))
    def test_insufficient_history_and_started_match(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); states=states_at(histories(current,4),current.isoformat())
        self.assertEqual(predict(states,'target',current.isoformat())['status'],'insufficient_data')
        self.assertEqual(predict(states,'target',(current+timedelta(days=1)).isoformat())['status'],'unavailable')
    def test_shrinkage_and_replay_determinism(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); rows=histories(current)
        a=predict(states_at(rows,current.isoformat()),'target',current.isoformat()); b=predict(states_at(list(reversed(rows)),current.isoformat()),'target',current.isoformat())
        self.assertEqual(digest(a),digest(b))


class PaperTests(unittest.TestCase):
    def test_vig_removal_prices_and_stale_quote_guard(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        prices=market(odds(current,2),current.isoformat())
        self.assertAlmostEqual(sum(prices['consensus'].values()),1)
        self.assertAlmostEqual(prices['consensus']['home'],1/3)
        self.assertEqual(market(odds(current), (current+timedelta(hours=2)).isoformat())['status'],'unavailable')
        self.assertEqual(market(odds(current)[:3],current.isoformat())['status'],'unavailable')
    def test_no_suggestion_without_model_and_thresholds(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); prices=market(odds(current),current.isoformat())
        self.assertEqual(suggestion({'status':'insufficient_data'},prices)['status'],'insufficient_data')
        model={'status':'experimental_prediction','probabilities':{'home':0.6,'draw':0.2,'away':0.2}}
        candidate=suggestion(model,prices)
        self.assertEqual(candidate['selection'],'home'); self.assertEqual(candidate['stake_units'],1)
        self.assertAlmostEqual(candidate['model_estimated_ev'],1.4)
        self.assertEqual(suggestion(model,market(odds(current,1.1),current.isoformat()))['status'],'no_paper_bet')
    def test_frozen_decision_settlement_and_no_rewrite(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp)/'edge.sqlite'); rows=histories(current)+odds(current); version=store.ingest(rows)
            (Path(tmp)/'status.json').write_text(__import__('json').dumps({'dataset_version':version}))
            first=scan(tmp,current); prediction=first['matches'][0]
            self.assertEqual(prediction['suggestion']['status'],'experimental_paper_candidate')
            repeated=scan(tmp,current+timedelta(minutes=10))
            self.assertEqual(prediction['prediction_id'],repeated['matches'][0]['prediction_id'])
            result=observation('target','result',{'home_goals':2,'away_goals':0,'status':'finished'},current+timedelta(hours=15))
            version=store.ingest([result],version); (Path(tmp)/'status.json').write_text(__import__('json').dumps({'dataset_version':version}))
            settled=scan(tmp,current+timedelta(hours=16)); self.assertEqual(settled['summary']['settled_paper_bets'],1)
            self.assertEqual(settled['summary']['paper_profit_units'],3)
            self.assertEqual(scan(tmp,current+timedelta(hours=17))['summary'],settled['summary'])
            paper=PaperLog(Path(tmp)/'paper.sqlite')
            for table in ('predictions','settlements'):
                with self.assertRaises(sqlite3.IntegrityError): paper.db.execute('DELETE FROM '+table)
            paper.close(); store.close()
    def test_sparse_data_never_freezes_fake_predictions(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp)/'edge.sqlite'); version=store.ingest(histories(current,4)+odds(current))
            (Path(tmp)/'status.json').write_text(__import__('json').dumps({'dataset_version':version}))
            report=scan(tmp,current); self.assertEqual(report['matches'][0]['model']['status'],'insufficient_data')
            paper=PaperLog(Path(tmp)/'paper.sqlite'); self.assertEqual(paper.db.execute('SELECT count(*) FROM predictions').fetchone()[0],0)
            paper.close(); store.close()

class AdditionalGuardTests(unittest.TestCase):
    def test_future_published_quotes_ignored_even_when_effective_earlier(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        rows=odds(current)
        for row in rows:
            row['available_at']=timestamp((current+timedelta(hours=1)).isoformat())
            row['observed_at']=row['available_at']; row['ingested_at']=row['available_at']
        self.assertEqual(market(rows,current.isoformat())['status'],'unavailable')
    def test_kickoff_revision_voids_the_paper_bet(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp)/'edge.sqlite'); rows=histories(current)+odds(current); version=store.ingest(rows)
            status=Path(tmp)/'status.json'; status.write_text(__import__('json').dumps({'dataset_version':version}))
            scan(tmp,current)
            revised=observation('target','fixture',{'home_team':'A','away_team':'B','competition_id':'soccer_epl','kickoff':(current+timedelta(hours=20)).isoformat()},current+timedelta(hours=1))
            result=observation('target','result',{'home_goals':2,'away_goals':0,'status':'finished'},current+timedelta(hours=23))
            version=store.ingest([revised,result],version); status.write_text(__import__('json').dumps({'dataset_version':version}))
            summary=scan(tmp,current+timedelta(days=1))['summary']
            self.assertEqual(summary['void_predictions'],1); self.assertEqual(summary['settled_paper_bets'],0); self.assertEqual(summary['paper_profit_units'],0)
            store.close()
