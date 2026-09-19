"""Six-task Chromium fixture and append-only oracle for Issue #57."""

from __future__ import annotations

import html
import http.server
import json
import threading
import time
import urllib.parse
from pathlib import Path


def workload(seed: int) -> list[dict]:
    return [
        {
            "task_id": f"task-{index}",
            "token": f"t{seed:06d}-{index}",
            "layout": "A" if index <= 3 else "B",
            "phase": (
                "cold" if index == 1 else
                "warm" if index in (2, 3) else
                "invalidation_repair" if index == 4 else
                "post_repair_warm"
            ),
        }
        for index in range(1, 7)
    ]


class Fixture:
    def __init__(self, root: Path, seed: int):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.history = self.root / "submission-history.jsonl"
        self.tasks = workload(seed)
        self.by_id = {row["task_id"]: row for row in self.tasks}
        self._lock = threading.Lock()
        fixture = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def _reply(self, status: int, body: bytes, title: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Agent-Interface-State", title)
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                parts = parsed.path.strip("/").split("/")
                task_id = f"task-{parts[1]}" if len(parts) == 2 and parts[0] == "task" else ""
                task = fixture.by_id.get(task_id)
                if task is None:
                    self._reply(404, b"<!doctype html><title>NOT FOUND</title>", "NOT FOUND")
                    return
                if task["layout"] == "A":
                    style = "main{margin:180px 0 0 55px}input{width:210px}button{margin-left:18px}"
                else:
                    style = ("body{background:#eef2f7}main{margin:330px 0 0 430px}"
                             "label{display:block;font-weight:bold}input{width:300px;height:30px}"
                             "button{display:block;margin:35px 0 0 190px;padding:12px 30px}")
                action = "/submit/" + task_id.removeprefix("task-")
                body = (
                    "<!doctype html><meta charset=utf-8>"
                    f"<title>AI INTEGRATED {html.escape(task_id)} READY</title>"
                    f"<style>{style}</style><main><h1>Observation fixture</h1>"
                    f"<form method=post action='{action}'><label>Value "
                    "<input name=value autofocus autocomplete=off></label>"
                    "<button type=submit>Save</button></form></main>"
                ).encode()
                self._reply(200, body, "READY")

            def do_POST(self):
                parsed = urllib.parse.urlparse(self.path)
                parts = parsed.path.strip("/").split("/")
                task_id = f"task-{parts[1]}" if len(parts) == 2 and parts[0] == "submit" else ""
                task = fixture.by_id.get(task_id)
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                values = urllib.parse.parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
                record = {
                    "schema": "integrated_efficiency_submission_v1",
                    "received_ns": time.perf_counter_ns(),
                    "task_id": task_id,
                    "layout": None if task is None else task["layout"],
                    "expected_token": None if task is None else task["token"],
                    "submitted_values": values.get("value", []),
                    "exact": bool(task and values == {"value": [task["token"]]}),
                }
                with fixture._lock:
                    with fixture.history.open("a", encoding="utf-8", newline="\n") as stream:
                        stream.write(json.dumps(record, sort_keys=True) + "\n")
                        stream.flush()
                title = "AI INTEGRATED SAVED" if record["exact"] else "AI INTEGRATED REJECTED"
                body = f"<!doctype html><title>{title}</title><h1>{title}</h1>".encode()
                self._reply(200 if record["exact"] else 422, body, title)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def goals(self) -> list[dict]:
        base = f"http://127.0.0.1:{self.server.server_port}"
        return [dict(row, url=f"{base}/task/{row['task_id'].removeprefix('task-')}")
                for row in self.tasks]

    def records(self) -> list[dict]:
        if not self.history.exists():
            return []
        return [json.loads(line) for line in self.history.read_text(encoding="utf-8").splitlines()]

    def evaluate(self) -> dict:
        records = self.records()
        counts = {row["task_id"]: 0 for row in self.tasks}
        for row in records:
            if row.get("task_id") in counts and row.get("exact") is True:
                counts[row["task_id"]] += 1
        unexpected = [row for row in records if not row.get("exact")]
        duplicates = {task: count for task, count in counts.items() if count > 1}
        missing = [task for task, count in counts.items() if count == 0]
        return {
            "schema": "integrated_efficiency_oracle_v1",
            "known_ns": time.perf_counter_ns(),
            "success": not unexpected and not duplicates and not missing and len(records) == 6,
            "record_count": len(records),
            "exact_counts": counts,
            "unexpected": unexpected,
            "duplicates": duplicates,
            "missing": missing,
        }

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
