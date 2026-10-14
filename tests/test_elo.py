import unittest
from edge.elo import Elo,blend
from edge.tracker import outcome_prediction

class EloTests(unittest.TestCase):
    def test_home_advantage_draw_normalization_and_conservation(self):
        model=Elo();p=model.forecast('a','b')['probabilities']
        self.assertAlmostEqual(sum(p.values()),1); self.assertGreater(p['home'],p['away']);self.assertGreater(p['draw'],0)
        model.observe('a','b',1,0);self.assertAlmostEqual(sum(model.ratings.values()),3000)
        self.assertGreater(model.ratings['a'],1500)
    def test_upset_updates_more_and_draw_direction(self):
        fav=Elo();fav.ratings={'a':1800,'b':1200};underdog=Elo();underdog.ratings=dict(fav.ratings)
        fav.observe('a','b',1,0);underdog.observe('a','b',0,1)
        self.assertGreater(1800-underdog.ratings['a'],fav.ratings['a']-1800)
        model=Elo();model.observe('a','b',0,0);self.assertLess(model.ratings['a'],1500)
    def test_forecast_does_not_mutate_and_invalid_result_rejected(self):
        model=Elo();model.forecast('unknown','other');self.assertEqual(model.ratings,{})
        for goals in [(True,0),(-1,0)]:
            with self.assertRaises(ValueError):model.observe('a','b',*goals)
    def test_winner_and_market_value_predictions_separate(self):
        model={'status':'experimental_prediction','probabilities':{'home':.6,'draw':.2,'away':.2},'winner_probabilities':{'home':.2,'draw':.25,'away':.55},'winner_model_version':'elo-winner-v1'}
        p=outcome_prediction(model,{'status':'unavailable'})
        self.assertEqual(p['selection'],'away');self.assertEqual(p['model_probability'],.55)
        self.assertEqual(blend(model['probabilities'],model['winner_probabilities'],1),model['winner_probabilities'])
