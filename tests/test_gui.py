import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
from edge.gui import handler,payload


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)
        (self.path/'tracker.json').write_text(json.dumps({'matches':[],'summary':{},'dataset_version':'test'}))
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler(self.path))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.thread.join(); self.tmp.cleanup()
    def request(self,path,method='GET',headers=None):
        client=HTTPConnection('127.0.0.1',self.server.server_port); client.request(method,path,headers=headers or {}); response=client.getresponse()
        status=response.status; headers=dict(response.getheaders()); body=response.read(); client.close(); return status,headers,body
    def test_live_api_returns_tracker_not_credentials_or_raw_archive(self):
        (self.path/'collector.env').write_text('SECRET_DO_NOT_RETURN')
        status,headers,body=self.request('/api/dashboard')
        self.assertEqual(status,200); self.assertEqual(json.loads(body)['report']['dataset_version'],'test')
        self.assertNotIn(b'SECRET_DO_NOT_RETURN',body); self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertNotIn('Access-Control-Allow-Origin',headers)
    def test_read_only_and_unknown_paths_blocked(self):
        self.assertEqual(self.request('/api/dashboard','POST')[0],405)
        self.assertEqual(self.request('/../../collector.env')[0],404)
        self.assertEqual(self.request('/api/dashboard',headers={'Host':'evil.example'})[0],403)
    def test_html_and_security_headers(self):
        status,headers,body=self.request('/')
        self.assertEqual(status,200); self.assertIn(b'Match desk',body); self.assertIn(b'Uncalibrated',body)
        self.assertEqual(headers['X-Frame-Options'],'DENY'); self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
    def test_empty_and_malformed_data_fail_honestly(self):
        (self.path/'tracker.json').unlink(); self.assertIsNone(payload(self.path)['report'])
        (self.path/'tracker.json').write_text('{bad')
        self.assertEqual(self.request('/api/dashboard')[0],503)
