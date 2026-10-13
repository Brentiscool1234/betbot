import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from edge.store import Store, validate, digest, timestamp
from edge.features import rolling
from edge.provider import convert, archive, load_archive
from edge.collect import collect, cadence


def record(mid='m',kind='fixture',available='2024-01-01T00:00:00Z',**kw):
    payload={'home_team':'A','away_team':'B','competition_id':'soccer_epl','kickoff':'2024-01-10T12:00:00Z'}
    if kind=='odds': payload={'bookmaker':'book','selection':'home','decimal_odds':2,'market':'1X2'}
    if kind=='result': payload={'home_goals':2,'away_goals':1,'status':'finished'}
    r={'match_id':mid,'kind':kind,'key':kind,'source':'test','source_ref':'test-archive',
       'effective_at':available,'available_at':available,'observed_at':'2026-01-01T00:00:00Z',
       'ingested_at':'2026-01-01T00:00:00Z','availability_basis':'verified_publication','payload':payload}
    r.update(kw); return r


class Integrity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name); self.store=Store(self.path/'edge.sqlite')
    def tearDown(self): self.store.close(); self.tmp.cleanup()
    def test_future_odds_correction_and_result_excluded(self):
        early=record(kind='odds',key='book:home')
        late=record(kind='odds',key='book:home',available='2024-01-10T11:00:00Z'); late['payload']['decimal_odds']=99
        score=record(kind='result',available='2024-01-10T14:00:00Z')
        version=self.store.ingest([record(),early,late,score])
        state=self.store.get_state('m','2024-01-09T12:00:00Z',version)
        self.assertEqual([r['payload']['decimal_odds'] for r in state if r['kind']=='odds'],[2])
        self.assertFalse(any(r['kind']=='result' for r in state))
    def test_observation_clock_is_distinct(self):
        version=self.store.ingest([record()])
        self.assertTrue(self.store.get_state('m','2024-01-09T00:00:00Z',version))
        self.assertEqual(self.store.get_state('m','2024-01-09T00:00:00Z',version,'observed'),[])
    def test_observed_only_cannot_be_backdated(self):
        with self.assertRaises(ValueError): validate(record(availability_basis='observed_only'))
    def test_timezone_order_and_prices(self):
        for change in ({'available_at':'2024-01-01'}, {'effective_at':'2025-01-01T00:00:00Z'}, {'observed_at':'2023-01-01T00:00:00Z'}):
            with self.assertRaises(ValueError): validate(record(**change))
        for price in (1,0,float('nan'),True):
            r=record(kind='odds'); r['payload']['decimal_odds']=price
            with self.assertRaises(ValueError): validate(r)
    def test_atomic_validation_no_partial_import(self):
        with self.assertRaises(ValueError): self.store.ingest([record(),record(available_at='bad')])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM records').fetchone()[0],0)
    def test_immutable_tables(self):
        version=self.store.ingest([record()])
        for table in ('records','datasets','members'):
            with self.assertRaises(sqlite3.IntegrityError): self.store.db.execute('DELETE FROM '+table)
            col='body' if table=='records' else 'id' if table=='datasets' else 'record'
            with self.assertRaises(sqlite3.IntegrityError): self.store.db.execute(f'UPDATE {table} SET {col}={col}')
    def test_versions_replay_order_independent_and_frozen(self):
        a,b=record(),record(kind='odds'); v=self.store.ingest([a,b])
        self.assertEqual(v,self.store.ingest([b,a,a]))
        before=digest(self.store.get_state('m','2024-01-09T00:00:00Z',v))
        newer=self.store.ingest([record(kind='result')],v)
        self.assertNotEqual(v,newer)
        self.assertEqual(before,digest(self.store.get_state('m','2024-01-09T00:00:00Z',v)))
        with self.assertRaises(ValueError): self.store.records('unknown')
    def test_rolling_excludes_current_future_and_late_publication(self):
        old=record('old'); old['payload']['kickoff']='2023-12-01T12:00:00Z'
        score=record('old',kind='result')
        future=record('future'); future['payload']['kickoff']='2024-01-20T12:00:00Z'
        late=record('late'); late['payload']['kickoff']='2023-12-10T12:00:00Z'
        late_score=record('late',kind='result',available='2024-01-10T13:00:00Z')
        version=self.store.ingest([record(),record(kind='result'),old,score,future,record('future',kind='result'),late,late_score])
        result=rolling(self.store,version,'m','2024-01-09T12:00:00Z')
        self.assertEqual(result['home']['matches'],1); self.assertEqual(result['home']['goals_for'],2)
    def test_missing_features_explicit(self):
        v=self.store.ingest([record()]); self.assertIsNone(rolling(self.store,v,'m','2024-01-09T00:00:00Z')['home']['points'])


def envelope(current):
    t=current.isoformat()
    return {'received_at':t,'quota':{'remaining':'1000'},'request':{'parameters':{'date':t}},'response':[
        {'id':'live','sport_key':'soccer_epl','commence_time':(current+timedelta(days=2)).isoformat(),
         'home_team':'A','away_team':'B','bookmakers':[{'key':'book','last_update':t,'markets':[
            {'key':'h2h','outcomes':[{'name':'A','price':2},{'name':'B','price':3},{'name':'Draw','price':4}]}]}]}]}


class ProviderTests(unittest.TestCase):
    def test_historical_evidence_and_future_update(self):
        current=datetime(2024,1,1,tzinfo=timezone.utc); e=envelope(current)
        e['response']={'timestamp':current.isoformat(),'data':e['response']}; e['received_at']='2026-01-01T00:00:00Z'
        rows=convert(e,True); self.assertEqual(len(rows),4)
        e['response']['data'][0]['bookmakers'][0]['last_update']='2024-01-02T00:00:00Z'
        with self.assertRaises(ValueError): convert(e,True)
    def test_inplay_prices_excluded(self):
        current=datetime(2024,1,1,tzinfo=timezone.utc); e=envelope(current)
        e['response'][0]['commence_time']=current.isoformat()
        self.assertEqual(len(convert(e)),1)
    def test_checksum_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            e=envelope(datetime.now(timezone.utc)); sha=archive(tmp,e); path=Path(tmp)/(sha+'.json')
            self.assertEqual(load_archive(path),e); path.write_text('{}')
            with self.assertRaises(ValueError): load_archive(path)
    def test_adaptive_cadence(self):
        current=datetime.now(timezone.utc)
        for seconds,expected in ((3600,300),(21600,900),(86400,3600),(86401,21600),(-1,21600)):
            self.assertEqual(cadence([{'commence_time':(current+timedelta(seconds=seconds)).isoformat()}],current),expected)
        self.assertEqual(cadence([],current),21600)
    def test_collection_not_due_no_network_and_crash_replay(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            result=collect(tmp,lambda:envelope(current),current)
            self.assertEqual(result['status'],'collected')
            def unwanted(): raise AssertionError('not-due must not make network request')
            self.assertEqual(collect(tmp,unwanted,current+timedelta(minutes=1))['status'],'not_due')
            archived=envelope(current+timedelta(hours=7)); sha=archive(Path(tmp)/'archives',archived)
            result=collect(tmp,lambda:envelope(current+timedelta(hours=8)),current+timedelta(hours=8))
            self.assertIn(sha,result['applied_archives'])
            store=Store(Path(tmp)/'edge.sqlite')
            self.assertEqual(len(store.records(result['dataset_version'])),12); store.close()
    def test_overlap_lock(self):
        import fcntl
        with tempfile.TemporaryDirectory() as tmp:
            with (Path(tmp)/'collector.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                self.assertEqual(collect(tmp)['status'],'locked')


if __name__=='__main__': unittest.main()

class BudgetTests(unittest.TestCase):
    def test_budget_blocks_network_and_persists_across_restart(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            collect(tmp,lambda:envelope(current),current,daily_limit=1)
            def unwanted(): raise AssertionError('budget must prevent request')
            paused=collect(tmp,unwanted,current+timedelta(hours=7),daily_limit=1)
            self.assertEqual(paused['status'],'paused_budget')
            self.assertEqual(json.loads((Path(tmp)/'budget.json').read_text())['daily_used'],1)
    def test_rollover_quota_and_monthly_cap(self):
        from edge.budget import Budget
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            budget=Budget(Path(tmp)/'budget.json',daily=1,monthly=2)
            self.assertIsNone(budget.reserve(current)); budget.reconcile({'last':'1','remaining':'1000'})
            self.assertIsNotNone(budget.reserve(current))
            self.assertIsNone(budget.reserve(current+timedelta(days=1)))
            self.assertEqual(budget.reserve(current+timedelta(days=2)),'monthly credit limit reached')
            self.assertIsNone(budget.reserve(datetime(2026,2,1,tzinfo=timezone.utc)))
            budget.reconcile({'last':'1','remaining':'100'})
            self.assertEqual(budget.reserve(datetime(2026,2,2,tzinfo=timezone.utc)),'provider quota reserve reached')

class OperationsTests(unittest.TestCase):
    def test_health_reports_budget_pause_and_staleness(self):
        from edge.health import check
        current=datetime(2026,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(check(tmp,current)['healthy'])
            collect(tmp,lambda:envelope(current),current,daily_limit=1)
            self.assertTrue(check(tmp,current)['healthy'])
            collect(tmp,lambda:envelope(current),current+timedelta(hours=7),daily_limit=1)
            health=check(tmp,current+timedelta(hours=7))
            self.assertFalse(health['healthy']); self.assertEqual(len(health['problems']),2)
    def test_historical_reuses_archive_without_index(self):
        from unittest.mock import patch
        from edge.historical import run
        current=datetime(2024,8,8,12,tzinfo=timezone.utc); e=envelope(current)
        e['request']['parameters']['date']='2024-08-08T12:00:00Z'
        e['response']={'timestamp':current.isoformat(),'data':e['response']}; e['received_at']='2026-01-01T00:00:00Z'
        with tempfile.TemporaryDirectory() as tmp:
            archive(Path(tmp)/'archives',e)
            with patch('edge.historical.fetch',side_effect=AssertionError('duplicate paid request')):
                result=run(tmp,target=1,max_requests=1)
            self.assertEqual(result['t24_demonstrations'],1)
