import json
import tempfile
import threading
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
from edge.refresh import RefreshManager,acquire


class RefreshTests(unittest.TestCase):
    def test_job_progress_shared_lock_cooldown_and_restart(self):
        started=threading.Event(); release=threading.Event(); current=datetime(2026,1,1,tzinfo=timezone.utc)
        def runner(directory,progress):
            progress('Fetching'); started.set(); release.wait(2)
            return [{'step':'test','status':'collected'}]
        with tempfile.TemporaryDirectory() as tmp:
            manager=RefreshManager(tmp,runner,lambda:current)
            result,status=manager.start(); self.assertEqual(status,202); started.wait(1)
            other=RefreshManager(tmp,runner,lambda:current)
            self.assertEqual(other.start()[1],409)
            release.set(); manager.thread.join(3)
            self.assertEqual(manager.status()['status'],'completed')
            self.assertEqual(manager.start()[1],429)
            manager.clock=lambda:current+timedelta(minutes=5)
            self.assertEqual(manager.start()[1],202); manager.thread.join(3)
    def test_partial_failure_keeps_tracker_recompute(self):
        with patch('edge.collect.collect',return_value={'status':'paused_budget','reason':'monthly cap'}),patch('edge.scores.collect_scores',side_effect=ValueError('provider unavailable')),patch('edge.bootstrap.run',return_value={'seasons':[]}),patch('edge.refresh.latest_openfootball_revision',return_value='a'*40),patch('edge.tracker.scan',return_value={'status':'experimental_paper_tracker'}) as tracker:
            outcomes=acquire('unused',lambda _:None)
            self.assertEqual(outcomes[0]['status'],'paused_budget'); self.assertEqual(outcomes[1]['status'],'failed')
            self.assertEqual(outcomes[-1]['status'],'experimental_paper_tracker'); tracker.assert_called_once()
    def test_interrupted_job_reported_on_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'data-refresh.json').write_text(json.dumps({'status':'running','started_at':'2026-01-01T00:00:00Z'}))
            manager=RefreshManager(tmp)
            self.assertEqual(manager.status()['status'],'failed')
    def test_http_acceptance_starts_only_authorized_job(self):
        from http.server import ThreadingHTTPServer
        from http.client import HTTPConnection
        from edge.gui import handler
        with tempfile.TemporaryDirectory() as tmp:
            manager=RefreshManager(tmp,lambda directory,progress:[{'status':'collected'}])
            server=ThreadingHTTPServer(('127.0.0.1',0),handler(tmp,manager)); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
            try:
                client=HTTPConnection('127.0.0.1',server.server_port); client.request('GET','/api/dashboard'); token=json.loads(client.getresponse().read())['refresh_token']; client.close()
                client=HTTPConnection('127.0.0.1',server.server_port)
                client.request('POST','/api/refresh',body='{"action":"refresh_data"}',headers={'Origin':'http://127.0.0.1:'+str(server.server_port),'Content-Type':'application/json','X-EDGE-CSRF':token})
                response=client.getresponse(); self.assertEqual(response.status,202); response.read(); client.close(); manager.thread.join(2)
                self.assertEqual(manager.status()['status'],'completed')
            finally: server.shutdown(); server.server_close(); thread.join()
