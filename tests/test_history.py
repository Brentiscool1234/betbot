import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from edge.history import update
from edge.coverage import diagnose
from test_predictions import histories
from edge.poisson import states_at,predict


class HistoryTests(unittest.TestCase):
    def test_daily_check_persists_success_and_runs_scanner(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=update(tmp,lambda:'a'*40,lambda directory,revision:{'seasons':[{'completed_results':10}]},lambda directory:{'status':'experimental_paper_tracker','matches':[{'model':{'status':'insufficient_data'}}]})
            self.assertEqual(result['status'],'completed'); self.assertEqual(result['completed_results'],10)
            self.assertEqual(result['model_ready'],0); self.assertTrue((Path(tmp)/'history-last-success.json').exists())
    def test_failure_preserves_last_success_and_does_not_claim_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            success=update(tmp,lambda:'a'*40,lambda directory,revision:{'seasons':[]},lambda directory:{'status':'experimental_paper_tracker','matches':[]})
            def unavailable(): raise ValueError('source unavailable')
            failed=update(tmp,unavailable)
            self.assertEqual(failed['status'],'failed'); self.assertEqual(failed['last_success'],success['last_success'])
    def test_gap_report_names_missing_venue_counts(self):
        current=datetime(2026,1,1,tzinfo=timezone.utc); states=states_at(histories(current,3),current.isoformat()); model=predict(states,'target',current.isoformat())
        fixture=next(r['payload'] for r in states['target'] if r['kind']=='fixture')
        report=diagnose(states,[{'match_id':'target','fixture':fixture,'model':model}],current.isoformat())
        entry=report['matches'][0]
        self.assertEqual(entry['home_shortfall'],2); self.assertEqual(entry['away_shortfall'],2)
        self.assertEqual(entry['league_shortfall'],47); self.assertEqual(report['model_ready'],0)

    def test_history_overlap_does_not_start_another_download(self):
        import fcntl
        with tempfile.TemporaryDirectory() as tmp:
            with (Path(tmp)/'history.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                self.assertEqual(update(tmp)['status'],'locked')
