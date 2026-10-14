import unittest
from edge.csv_results import convert
from edge.store import validate
from edge.form import Form
from edge.research.forest_study import features

class CsvAndFeaturesTests(unittest.TestCase):
    def test_aliases_observed_receipt_and_skip_same_day(self):
        raw=b'Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR\nE0,01/01/2026,15:00,Man City,Man United,2,0,H\nE0,03/01/2026,15:00,Man City,Man United,1,0,H\n'
        records,skip=convert(raw,'2026-01-03T20:00:00+00:00',[])
        self.assertEqual(len(records),2);self.assertEqual(skip['future_or_same_day'],1)
        self.assertEqual(records[0]['payload']['home_team'],'Manchester City')
        for r in records:
            validate(r);self.assertEqual(r['observed_at'],r['available_at'])
    def test_conflicts_do_not_overwrite_and_other_leagues_rejected(self):
        raw=b'Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\nE0,01/01/2026,Man City,Man United,2,0,H\n'
        records,_=convert(raw,'2026-01-03T20:00:00+00:00',[])
        changed=raw.replace(b',2,0,H',b',0,2,A')
        result,skip=convert(changed,'2026-01-04T20:00:00+00:00',records)
        self.assertEqual(result,[]);self.assertEqual(skip['score_conflict'],1)
        with self.assertRaises(ValueError):convert(raw.replace(b'E0,',b'E1,'),'2026-01-03T20:00:00+00:00',[])
    def test_current_and_same_day_results_not_features(self):
        config={'k':40,'home_advantage':50,'draw_parameter':.75}
        rows=[{'day':'2026-01-01','home':'a','away':'b','hg':2,'ag':0}, {'day':'2026-01-01','home':'a','away':'c','hg':0,'ag':1}]
        first=features(rows,config);rows[0]['hg']=8;changed=features(rows,config)
        self.assertEqual([r['x'] for r in first],[r['x'] for r in changed])
        future=dict(rows[0],day='2026-02-01',hg=99)
        self.assertEqual([r['x'] for r in changed],[r['x'] for r in features(rows+[future],config)[:2]])
    def test_form_limited_history(self):
        form=Form()
        for _ in range(12):form.observe('a','b',2,0)
        self.assertEqual(form.summary('a')['matches'],5);self.assertEqual(form.summary('a')['points_per_match'],3)
