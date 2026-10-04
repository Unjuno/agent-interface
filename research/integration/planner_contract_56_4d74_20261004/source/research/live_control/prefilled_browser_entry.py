"""Visible pre-existing draft fixture; server stores input without expected answer."""
import http.server,threading
import interactive_v27 as runtime


def fixture_server(path):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,body):
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_GET(self):
            self.send(b'<!doctype html><title>AI FORM READY</title><h1>Observation fixture</h1>'
                b'<p>There is an unsaved draft. Replace it with the requested value before saving.</p>'
                b'<form method="post" action="/submit"><label>Value '
                b'<input name="value" value="old-draft-42" autofocus></label><button>Save</button></form>')
        def do_POST(self):
            data=self.rfile.read(int(self.headers['Content-Length']))
            path.write_bytes(data)
            self.send(b'<!doctype html><title>AI FORM SAVED</title><h1>Submission received</h1>')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server


runtime.suite.fixture_server=fixture_server
runtime.main()
