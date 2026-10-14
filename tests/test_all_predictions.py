import unittest
import tempfile
from pathlib import Path
from edge.tracker import outcome_prediction,PaperLog

class AllPredictionTests(unittest.TestCase):
    def test_prediction_without_prices_and_draw(self):
        p=outcome_prediction({'status':'experimental_prediction','probabilities':{'home':.2,'draw':.5,'away':.3}}, {'status':'unavailable'})
        self.assertEqual(p['selection'],'draw')
        self.assertEqual(p['simulation_status'],'waiting_for_fresh_odds')
    def test_below_value_pick_still_simulated(self):
        p=outcome_prediction({'status':'experimental_prediction','probabilities':{'home':.6,'draw':.2,'away':.2}}, {'status':'available','best_prices':{'home':{'decimal_odds':1.2,'bookmaker':'test'}}})
        self.assertEqual(p['simulation_status'],'ready')
        self.assertLess(p['model_estimated_ev'],0)
    def test_accuracy_without_market_and_immutable_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=PaperLog(Path(tmp)/'test.sqlite')
            body={'match_id':'match','prediction_timestamp':'2026-01-01T00:00:00.000000+00:00','fixture':{'kickoff':'2026-01-02T00:00:00.000000+00:00'},'model':{'probabilities':{'home':.6,'draw':.2,'away':.2}},'market':{'status':'unavailable'},'suggestion':{'status':'accuracy_only'},'outcome_prediction':{'selection':'home'}}
            first=log.freeze(body)
            changed=dict(body,outcome_prediction={'selection':'away'})
            self.assertEqual(log.freeze(changed),first)
            time='2026-01-03T00:00:00.000000+00:00'
            result={'kind':'result','available_at':time,'observed_at':time,'effective_at':time,'payload':{'home_goals':2,'away_goals':0}}
            log.settle({'match':[result]},time)
            s=log.summary();self.assertEqual(s['prediction_accuracy'],1);self.assertEqual(s['settled_paper_bets'],0);self.assertIsNone(s['mean_market_brier']);log.close()
    def test_ten_dollar_win_and_loss(self):
        for outcome,expected in [(2,7),(0,-10)]:
            with tempfile.TemporaryDirectory() as tmp:
                log=PaperLog(Path(tmp)/'test.sqlite')
                body={'match_id':'m','prediction_timestamp':'2026-01-01T00:00:00.000000+00:00','fixture':{'kickoff':'2026-01-02T00:00:00.000000+00:00'},'model':{'probabilities':{'home':.6,'draw':.2,'away':.2}},'market':{'consensus':{'home':.5,'draw':.25,'away':.25}},'suggestion':{'selection':'home','decimal_odds':1.7}}
                log.freeze(body);time='2026-01-03T00:00:00.000000+00:00'
                r={'kind':'result','available_at':time,'effective_at':time,'observed_at':time,'payload':{'home_goals':outcome,'away_goals':1}}
                log.settle({'m':[r]},time);self.assertAlmostEqual(log.summary()['paper_profit_dollars'],expected);log.close()
