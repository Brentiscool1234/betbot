import unittest
from datetime import date,timedelta
from edge.research.dynamic import Dynamic,corrected_probabilities,temperature,residual_proposal
from edge.research.compare import compare


class ResearchTests(unittest.TestCase):
    def test_low_score_correction_increases_draw_probability(self):
        base=corrected_probabilities(1.5,1.2,0); adjusted=corrected_probabilities(1.5,1.2,-.08)
        self.assertAlmostEqual(sum(adjusted.values()),1); self.assertGreater(adjusted['draw'],base['draw'])
        self.assertTrue(all(p>=0 for p in adjusted.values()))
        with self.assertRaises(ValueError): corrected_probabilities(5,5,-1)
    def test_opponent_strength_changes_goal_residual_update(self):
        strong=Dynamic(); weak=Dynamic()
        strong.team('opponent','2025-01-01')['weakness']=-.4
        weak.team('opponent','2025-01-01')['weakness']=.4
        strong.observe('home','opponent','2025-01-01',2,1); weak.observe('home','opponent','2025-01-01',2,1)
        self.assertGreater(strong.teams['home']['attack'],weak.teams['home']['attack'])
    def test_time_decay_and_backward_clock_guard(self):
        model=Dynamic(half_life=365); model.team('A','2024-01-01')['attack']=.4
        model.forecast('A','B','2024-12-31')
        self.assertAlmostEqual(model.teams['A']['attack'],.2)
        with self.assertRaises(ValueError): model.forecast('A','B','2024-01-01')
    def test_unknown_history_means_no_market_residual_edge(self):
        market={'home':.5,'draw':.25,'away':.25}; members=[{'home':.9,'draw':.05,'away':.05}]
        result=residual_proposal(market,members,[1.],0,{'home':2,'draw':4,'away':4})
        self.assertEqual(result['market_residual_weight'],0); self.assertEqual(result['probabilities'],market)
        self.assertAlmostEqual(sum(temperature(market,1.2).values()),1)
    def test_test_label_does_not_change_earlier_forecast_or_validation_choice(self):
        matches=[]
        for i in range(240):
            day=(date(2024,8,1)+timedelta(days=i)).isoformat()
            matches.append({'day':day,'home':'A','away':'B','hg':i%3,'ag':i%2,'season':'2024-25'})
        for i in range(40):
            day=(date(2025,8,1)+timedelta(days=i)).isoformat()
            matches.append({'day':day,'home':'A','away':'B','hg':i%3,'ag':i%2,'season':'2025-26'})
        original=compare(matches)
        changed=[dict(m) for m in matches]; changed[-1]['hg']=9
        updated=compare(changed)
        self.assertEqual(original['calibration_temperatures'],updated['calibration_temperatures'])
        self.assertEqual(original['ensemble_weights'],updated['ensemble_weights'])
        self.assertEqual(original['test_predictions'][0],updated['test_predictions'][0])
        self.assertEqual(original['test_predictions'][-1]['candidate'],updated['test_predictions'][-1]['candidate'])

    def test_market_study_rejects_unbounded_requests_without_fetching(self):
        from edge.research.market_study import run
        with self.assertRaises(ValueError): run('unused',max_requests=21)
        with self.assertRaises(ValueError): run('unused',target=101)
