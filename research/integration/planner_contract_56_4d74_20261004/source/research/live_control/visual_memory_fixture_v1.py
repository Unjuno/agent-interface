"""Deterministic Chromium target/decoy pages for visual-memory ablation."""
import html
import http.server
import json
import threading
import time
import urllib.parse
from pathlib import Path


SCENARIOS = ("shifted", "duplicate", "restyled_trap")


class Fixture:
    def __init__(self, root, seed):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.seed = seed; self.token = f"t{seed:06d}"
        self.history = self.root / "history.jsonl"; self.lock = threading.Lock()
        fixture = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_args): return

            def reply(self, status, text, title):
                body = (f"<!doctype html><meta charset=utf-8><title>{title}</title>"
                        f"<h1>{html.escape(text)}</h1>").encode()
                self.send_response(status); self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                scenario = urllib.parse.urlparse(self.path).path.strip("/")
                if scenario not in SCENARIOS:
                    self.reply(404, "missing", "NOT FOUND"); return
                if scenario == "shifted":
                    real, decoy = ("left:135px;top:165px", "left:650px;top:205px")
                    real_style, decoy_label = "", "Save preview"
                elif scenario == "duplicate":
                    real, decoy = ("left:650px;top:205px", "left:135px;top:165px")
                    real_style, decoy_label = "", "Save"
                else:
                    real, decoy = ("left:135px;top:165px", "left:650px;top:205px")
                    real_style, decoy_label = "background:#2563eb;color:white;border-color:#1d4ed8", "Save"
                token = html.escape(fixture.token)
                page = f"""<!doctype html><meta charset=utf-8>
<title>AI MEMORY {scenario} READY</title>
<style>
body{{font:16px Arial;background:#f3f4f6;margin:0}} .card{{position:absolute;width:360px;height:235px;background:white;border:2px solid #9ca3af;border-radius:8px;padding:22px;box-sizing:border-box}}
h1{{font-size:24px;margin:0 0 16px}} label{{display:block;margin:12px 0}} input{{width:265px;height:30px}} button{{margin-top:18px;padding:8px 24px;font-size:16px}}
</style>
<section class=card style='{real}'><h1>Submission form</h1><p>Submit the authorized Value record.</p><form method=post action='/submit/{scenario}'><label>Value <input name=value value='{token}' readonly></label><button style='{real_style}' type=submit>Save</button></form></section>
<section class=card style='{decoy}'><h1>Preview card</h1><p>This preview must remain untouched.</p><form method=post action='/decoy/{scenario}'><label>Preview <input name=value value='{token}' readonly></label><button type=submit>{decoy_label}</button></form></section>""".encode()
                self.send_response(200); self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(page))); self.end_headers(); self.wfile.write(page)

            def do_POST(self):
                parts = urllib.parse.urlparse(self.path).path.strip("/").split("/")
                kind, scenario = parts if len(parts) == 2 else ("invalid", "invalid")
                length = int(self.headers.get("Content-Length", "0")); raw = self.rfile.read(length)
                values = urllib.parse.parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
                row = {"known_ns": time.perf_counter_ns(), "kind": kind, "scenario": scenario,
                       "values": values, "exact": kind == "submit" and scenario in SCENARIOS
                       and values == {"value": [fixture.token]}}
                with fixture.lock:
                    with fixture.history.open("a", encoding="utf-8", newline="\n") as stream:
                        stream.write(json.dumps(row, sort_keys=True) + "\n"); stream.flush()
                title = "AI MEMORY SAVED" if row["exact"] else "AI MEMORY DECOY"
                self.reply(200 if row["exact"] else 422, title, title)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()

    def url(self, scenario): return f"http://127.0.0.1:{self.server.server_port}/{scenario}"
    def records(self):
        return [] if not self.history.exists() else [json.loads(line) for line in self.history.read_text(encoding="utf-8").splitlines()]
    def close(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)

