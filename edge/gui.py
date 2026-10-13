"""Read-only EDGE dashboard; loopback only, access through an SSH tunnel."""
import argparse
import json
import secrets
from urllib.parse import urlsplit
from .refresh import RefreshManager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .store import canonical


def payload(directory):
    directory=Path(directory)
    def read(name):
        path=directory/name
        return json.loads(path.read_text()) if path.exists() else None
    return {'report':read('tracker.json'),'collector':read('status.json'),'scores':read('scores-status.json'),
            'budget':read('budget.json'),'bootstrap':read('bootstrap-report.json'),
            'budget_status':read('budget-status.json'),'scores_budget_status':read('scores-budget-status.json'),
            'refresh':read('data-refresh.json'),'connection':'vps','mode':'experimental_paper'}


def handler(directory,manager=None):
    manager=manager or RefreshManager(directory)
    token=secrets.token_urlsafe(32)
    class Dashboard(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.do_GET()
        def do_GET(self):
            host=self.headers.get('Host','').split(':',1)[0].lower()
            if host not in ('127.0.0.1','localhost'):
                self.send_error(403,'Use the local SSH tunnel address'); return
            path=self.path.split('?',1)[0]
            if path in ('/','/index.html'):
                body=Path(__file__).with_name('gui.html').read_bytes(); content='text/html; charset=utf-8'; status=200
            elif path=='/api/dashboard':
                try: body=canonical(dict(payload(directory),refresh_token=token)).encode(); status=200
                except (OSError,ValueError,KeyError): body=b'{"error":"Dashboard data unavailable; collector may be writing. Retry shortly."}'; status=503
                content='application/json; charset=utf-8'
            elif path=='/favicon.ico': body=b''; content='image/x-icon'; status=204
            else: body=b'Not found'; content='text/plain'; status=404
            self.send_response(status)
            self.send_header('Content-Type',content); self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer'); self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            if self.command != 'HEAD': self.wfile.write(body)
        def do_POST(self):
            host=self.headers.get('Host','')
            origin=self.headers.get('Origin','')
            parsed=urlsplit(origin)
            if host.split(':',1)[0].lower() not in ('127.0.0.1','localhost') or parsed.scheme!='http' or parsed.netloc!=host:
                self.send_error(403,'Same-origin local access required'); return
            if not secrets.compare_digest(self.headers.get('X-EDGE-CSRF',''),token):
                self.send_error(403,'Refresh the dashboard before requesting data'); return
            if self.path!='/api/refresh': self.send_error(405,'Unsupported dashboard action'); return
            if self.headers.get('Content-Type')!='application/json': self.send_error(415,'JSON required'); return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<2 or length>128: raise ValueError()
                request=json.loads(self.rfile.read(length))
                if request!={'action':'refresh_data'}: raise ValueError()
            except (ValueError,TypeError): self.send_error(400,'Invalid refresh request'); return
            result,status=manager.start(); body=canonical(result).encode()
            self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(body)
        def log_message(self,*args): pass
    return Dashboard


def main():
    p=argparse.ArgumentParser(); p.add_argument('--directory',default='data/prospective'); p.add_argument('--port',type=int,default=8765); args=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(args.directory))
    print('EDGE private dashboard listening at http://127.0.0.1:'+str(args.port),flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__=='__main__': main()
