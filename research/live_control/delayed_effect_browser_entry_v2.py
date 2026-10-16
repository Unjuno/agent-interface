"""Delayed saved effect submitted by fetch, with no navigation or loading UI."""
import argparse
import http.server
import json
import threading
import time
from pathlib import Path
import checkpoint_cause_interactive_v1 as runtime


def fixture_server(path, log_path, delay_s=5.0):
    lock = threading.Lock()
    body = (b'<!doctype html><title>AI FORM READY</title><h1>Observation fixture</h1>'
            b'<p>Save the requested value.</p><form id="f"><label>Value '
            b'<input name="value" autofocus></label><button>Save</button></form>'
            b'<script>f.addEventListener("submit",e=>{e.preventDefault();'
            b'fetch("/submit",{method:"POST",body:new URLSearchParams(new FormData(f))});});</script>')

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send_page(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def append(self, record):
            with lock:
                with log_path.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(record) + '\n')

        def do_GET(self):
            self.send_page()

        def do_POST(self):
            data = self.rfile.read(int(self.headers['Content-Length']))
            self.append({'event': 'received', 'known_ns': time.perf_counter_ns(),
                         'bytes': len(data)})
            time.sleep(delay_s)
            path.write_bytes(data)
            self.append({'event': 'committed', 'known_ns': time.perf_counter_ns(),
                         'bytes': len(data)})
            self.send_response(204)
            self.end_headers()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--out', type=Path, required=True)
    args, _ = parser.parse_known_args()
    attempt_log = args.out.resolve() / 'delayed-effects.jsonl'
    runtime.suite.fixture_server = lambda path: fixture_server(path, attempt_log)
    runtime.main()

