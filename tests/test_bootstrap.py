import unittest
from datetime import datetime,timezone,timedelta
from edge.bootstrap import convert_bootstrap,team,REVISION
from edge.poisson import predict,states_at
from test_predictions import observation,histories


def envelope():
    return {'received_at':'2026-10-13T18:00:00Z','season':'2025-26','revision':REVISION,'response':{
      'name':'English Premier League 2025/26','matches':[
       {'date':'2026-05-01','time':'20:00','team1':'AFC Bournemouth','team2':'Fulham FC','score':{'ft':[2,1]}},
       {'date':'2026-10-14','time':'20:00','team1':'Arsenal FC','team2':'Chelsea FC','score':{'ft':[9,0]}},
       {'date':'2026-05-02','time':'20:00','team1':'Arsenal FC','team2':'Fulham FC','score':None}]}}


class BootstrapTests(unittest.TestCase):
    def test_receipt_only_aliases_timezone_and_future_score_exclusion(self):
        rows,skipped=convert_bootstrap(envelope(),[])
        self.assertEqual(len(rows),2); self.assertEqual(skipped['future'],1); self.assertEqual(skipped['unfinished'],1)
        self.assertEqual(rows[0]['payload']['home_team'],'Bournemouth')
        self.assertEqual(rows[0]['payload']['kickoff'],'2026-05-01T19:00:00.000000+00:00')
        self.assertFalse(states_at(rows,'2026-10-13T17:59:59Z'))
        self.assertTrue(states_at(rows,'2026-10-13T18:00:00Z'))
    def test_provider_event_mapping_and_conflicting_score(self):
        t=datetime(2026,5,1,19,tzinfo=timezone.utc)
        fixture=observation('the-odds-api:existing','fixture',{'home_team':'Bournemouth','away_team':'Fulham','competition_id':'soccer_epl','kickoff':t.isoformat()},t-timedelta(days=1))
        rows,_=convert_bootstrap(envelope(),[fixture]); self.assertEqual(rows[0]['match_id'],fixture['match_id'])
        score=observation(fixture['match_id'],'result',{'home_goals':3,'away_goals':1,'status':'finished'},t+timedelta(hours=3)); score['source']='the-odds-api'
        rows,skipped=convert_bootstrap(envelope(),[fixture,score]); self.assertEqual(rows,[]); self.assertEqual(skipped['conflicting_score'],1)
    def test_wrong_competition_duplicate_and_invalid_score_rejected(self):
        e=envelope(); e['response']['name']='Other League'
        with self.assertRaises(ValueError): convert_bootstrap(e,[])
        e=envelope(); e['response']['matches'].append(e['response']['matches'][0])
        with self.assertRaises(ValueError): convert_bootstrap(e,[])
        e=envelope(); e['response']['matches'][0]['score']['ft']=[True,1]
        with self.assertRaises(ValueError): convert_bootstrap(e,[])
    def test_duplicate_events_not_double_counted_and_conflicts_excluded(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); rows=histories(current)
        duplicates=[]
        for r in rows[:2]: duplicates.append(dict(r,match_id='duplicate'))
        model=predict(states_at(rows+duplicates,current.isoformat()),'target',current.isoformat())
        self.assertEqual(model['history_counts']['league'],60)
        duplicates[1]['payload']=dict(duplicates[1]['payload'],home_goals=9)
        model=predict(states_at(rows+duplicates,current.isoformat()),'target',current.isoformat())
        self.assertEqual(model['history_counts']['league'],59); self.assertEqual(model['history_counts']['conflicting_events_excluded'],1)
