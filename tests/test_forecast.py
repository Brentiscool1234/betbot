import copy
import json
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from edge.forecast import predict,prepare,MODEL_VERSION
from edge.poisson import states_at
from edge.tracker import market,suggestion,scan,PaperLog,PAPER_FILENAME
from edge.store import Store,digest
from test_predictions import histories,odds,observation


class ForecastIntegrationTests(unittest.TestCase):
    def test_active_formula_uses_market_and_remains_normalized(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); rows=histories(current)+odds(current)
        states=states_at(rows,current.isoformat()); prices=market(states['target'],current.isoformat())
        result=predict(states,'target',current.isoformat(),prices)
        self.assertEqual(result['model_version'],MODEL_VERSION); self.assertTrue(result['market_anchor_available'])
        self.assertAlmostEqual(sum(result['probabilities'].values()),1)
        self.assertLess(abs(result['probabilities']['home']-prices['consensus']['home']),abs(result['football_probabilities']['home']-prices['consensus']['home']))
    def test_future_score_and_target_result_do_not_affect_training(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); rows=histories(current)+odds(current)
        states=states_at(rows,current.isoformat()); prices=market(states['target'],current.isoformat())
        expected=predict(states,'target',current.isoformat(),prices)
        future=observation('prior-0','result',{'home_goals':9,'away_goals':0,'status':'finished'},current+timedelta(seconds=1))
        target=observation('target','result',{'home_goals':9,'away_goals':0,'status':'finished'},current)
        changed=states_at(rows+[future,target],current.isoformat())
        self.assertEqual(expected,predict(changed,'target',current.isoformat(),prices))
    def test_context_with_another_cutoff_rejected(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); states=states_at(histories(current),current.isoformat())
        context=prepare(states,current.isoformat())
        with self.assertRaises(ValueError): predict(states,'target',(current+timedelta(minutes=1)).isoformat(),{'status':'unavailable'},context)
    def test_scenario_negative_ev_prevents_otherwise_qualifying_signal(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); prices=market(odds(current),current.isoformat())
        model={'status':'experimental_prediction','probabilities':{'home':.6,'draw':.2,'away':.2},'scenario_minimum_estimated_ev':{'home':-.01,'draw':-.1,'away':-.1}}
        self.assertEqual(suggestion(model,prices)['status'],'no_paper_bet')
    def test_old_log_is_preserved_and_new_model_uses_separate_cohort(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); old=PaperLog(root/'paper-v2.sqlite'); old.close()
            store=Store(root/'edge.sqlite'); version=store.ingest(histories(current)+odds(current)); (root/'status.json').write_text(json.dumps({'dataset_version':version}))
            report=scan(root,current)
            self.assertEqual(report['matches'][0]['model']['model_version'],MODEL_VERSION)
            self.assertIn('baseline_model',report['matches'][0]); self.assertTrue((root/PAPER_FILENAME).exists())
            self.assertEqual(len(report['previous_policy_summaries']),1)
            old=PaperLog(root/'paper-v2.sqlite'); self.assertEqual(old.db.execute('SELECT count(*) FROM predictions').fetchone()[0],0)
            old.close(); store.close()
