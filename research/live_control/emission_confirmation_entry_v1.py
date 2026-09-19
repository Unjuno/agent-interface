"""Test-only server requires visible confirmation before storing a replacement."""
import html
import http.server
import json
import threading
import time
import urllib.parse
import cause_servo_interactive_v4 as runtime


def fixture_server(path):
    lock = threading.Lock()
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send(self, body):
            body = body.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def form(self, value, confirmation):
            heading = 'Replacement needs confirmation' if confirmation else 'Observation fixture'
            message = ('Nothing has been saved. Confirm replacement of the existing draft, then save again.'
                       if confirmation else 'Replace the unsaved draft with the requested value before saving.')
            checkbox = ('<p><label><input type="checkbox" name="confirm" value="yes">'
                        'Confirm replacement</label></p>' if confirmation else '')
            return ('<!doctype html><title>AI FORM READY</title><h1>'+heading+'</h1><p>'+message+'</p>'
                    '<form method="post" action="/submit"><label>Value <input name="value" value="'+
                    html.escape(value, quote=True)+'" autofocus></label>'+checkbox+'<button>Save</button></form>')
        def do_GET(self):
            self.send(self.form('old-draft-42', False))
        def do_POST(self):
            data = self.rfile.read(int(self.headers['Content-Length']))
            fields = urllib.parse.parse_qs(data.decode('utf-8'), keep_blank_values=True)
            accepted = fields.get('confirm') == ['yes'] and len(fields.get('value', [])) == 1
            with lock:
                with path.with_name('submission-attempts.jsonl').open('a') as log:
                    log.write(json.dumps(dict(received_ns=time.perf_counter_ns(), fields=fields,
                                              accepted=accepted))+'\n')
                if accepted:
                    # Ordinary evaluator sees only the committed value; confirmation is server policy.
                    path.write_text(urllib.parse.urlencode({'value': fields['value'][0]}))
            self.send('<!doctype html><title>AI FORM SAVED</title><h1>Submission received</h1>'
                      if accepted else self.form(fields.get('value', [''])[0], True))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


runtime.suite.fixture_server = fixture_server
runtime.main()
