"""Durable checked-input client used by all integrated comparison arms."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once


HERE = Path(__file__).resolve().parent


def first(records, event):
    return next(row for row in records if row.get("event") == event)


class RuntimeClient:
    def __init__(self, root: Path, seed: int):
        self.root = Path(root)
        self.seed = seed
        self.runtime = self.root / "runtime"
        self.errors = None
        self.process = None
        self.temporary = None
        self.journal = None
        self.endpoint = None
        self.ready = None
        self.programs = []
        self.durable_calls = 0

    def start(self):
        self.root.mkdir(parents=True, exist_ok=False)
        self.errors = (self.root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
        self.process = subprocess.Popen([
            sys.executable, "-u", str(HERE / "integrated_efficiency_socket_v1.py"),
            "integrated-efficiency-chromium-v1", "serve", "--", "--app", "chromium",
            "--seed", str(self.seed), "--out", str(self.runtime),
        ], stdout=subprocess.PIPE, stderr=self.errors, text=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="integrated-efficiency-client-")
        self.journal = Path(self.temporary.name) / "journal.jsonl"
        self.endpoint = json.loads(self.process.stdout.readline())
        initial = request_once(self.endpoint["socket"], start(self.endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        self.ready = first(initial["reply"]["records"], "ready")
        initialize(self.journal, initial["continuation"])
        return self

    def call(self, spec):
        started = time.perf_counter_ns()
        result = run(self.journal, spec)
        ended = time.perf_counter_ns()
        self.durable_calls += 1
        assert result["state"]["pending"] is None
        return result, started, ended

    def clock(self):
        result, _started, _ended = self.call({"command": {"op": "clock"}, "timeout": 3})
        return result["state"]["last_resolution"]["clock"]

    def submit(self, label, steps, timeout=10):
        current = self.clock()
        result, started, ended = self.call({"command": {"op": "submit",
            "expected_sequence": current["sequence"],
            "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
            "steps": steps}, "timeout": timeout})
        records = result["reply"]["records"]
        terminal = first(records, "terminal")
        record = {"label": label, "started_ns": started, "ended_ns": ended,
                  "terminal": terminal,
                  "observations": [row for row in records if row.get("event") == "observation"],
                  "pointer_admissions": [row for row in records if row.get("event") ==
                                          "pointer_admission"],
                  "target_checks": [row for row in records if row.get("event") ==
                                    "target_handle_checked"],
                  "point_mints": [row for row in records if row.get("event") ==
                                  "target_handle_minted_from_point"]}
        self.programs.append(record)
        return record

    def navigate(self, task):
        navigation = self.submit("navigate-" + task["task_id"], [
            {"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": task["url"]},
            {"op": "key", "key": "Return"},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
        ])
        if navigation["terminal"]["status"] != "completed":
            raise RuntimeError("navigation failed")
        source = self.submit("source-" + task["task_id"], [{"op": "observe"}])
        return source["observations"][-1]

    def mint(self, layout, source, grounding, prefix):
        normalized = re.sub(r"[^a-z0-9_]", "_", prefix.lower()).strip("_")
        if not normalized or not normalized[0].isalpha():
            raise ValueError("prefix must normalize to a letter-led target alias")
        normalized = normalized[:25]
        aliases = {"field": normalized + "_field", "submit": normalized + "_submit"}
        for kind in ("field", "submit"):
            row = self.submit("mint-" + aliases[kind], [{
                "op": "target_handle_mint_from_point", "name": aliases[kind],
                "coordinate_frame": "window_content", "source_sequence": source["sequence"],
                "point": grounding[kind + "_point"],
                "region_size": [24, 38] if kind == "field" else [24, 14],
                "ttl_ms": 300000, "freshness_ms": 1500, "search_radius": 0,
                "allowed_transformations": ["window_translation"],
            }])
            if row["terminal"]["status"] != "completed" or len(row["point_mints"]) != 1:
                return None, row
        return aliases, None

    def check(self, alias, offset, label):
        row = self.submit(label, [{"op": "observe_target_handle",
                                   "target_handle": alias, "offset": offset}])
        return row["target_checks"][0], row

    def execute_handles(self, task, aliases):
        started = time.perf_counter_ns()
        first_check, _ = self.check(aliases["field"], [12, 19],
                                    "check-field-" + task["task_id"])
        if not first_check["eligible"]:
            return {"status": "safe_yield", "reason": "missing_symbol",
                    "completed_actions": 0, "started_ns": started,
                    "ended_ns": time.perf_counter_ns()}
        entered = self.submit("enter-" + task["task_id"], [
            {"op": "pointer_click_target", "target_handle": aliases["field"],
             "offset": [12, 19], "button": 1, "duration_ms": 80},
            {"op": "chord", "modifier": "Control_L", "key": "a"},
            {"op": "text", "text": task["token"]},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
        ])
        if entered["terminal"]["status"] != "completed":
            return {"status": "safe_yield", "reason": "execution_failed",
                    "completed_actions": 0, "started_ns": started,
                    "ended_ns": time.perf_counter_ns()}
        submit_check, _ = self.check(aliases["submit"], [12, 7],
                                     "check-submit-" + task["task_id"])
        if not submit_check["eligible"]:
            return {"status": "safe_yield", "reason": "missing_symbol",
                    "completed_actions": 1, "started_ns": started,
                    "ended_ns": time.perf_counter_ns()}
        saved = self.submit("submit-" + task["task_id"], [
            {"op": "pointer_click_target", "target_handle": aliases["submit"],
             "offset": [12, 7], "button": 1, "duration_ms": 80},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
        ])
        status = "completed" if saved["terminal"]["status"] == "completed" else "safe_yield"
        return {"status": status,
                **({} if status == "completed" else
                   {"reason": "execution_failed", "completed_actions": 1}),
                "started_ns": started, "ended_ns": time.perf_counter_ns()}

    def execute_plain(self, task, grounding):
        started = time.perf_counter_ns()
        field = grounding["field_point"]
        submit = grounding["submit_point"]
        row = self.submit("plain-batch-" + task["task_id"], [
            {"op": "pointer_click", "x": field[0], "y": field[1],
             "button": 1, "duration_ms": 80},
            {"op": "chord", "modifier": "Control_L", "key": "a"},
            {"op": "text", "text": task["token"]},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
            {"op": "pointer_click", "x": submit[0], "y": submit[1],
             "button": 1, "duration_ms": 80},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
        ])
        return {"status": "completed" if row["terminal"]["status"] == "completed" else "failed",
                "started_ns": started, "ended_ns": time.perf_counter_ns()}

    def finish(self, request_id):
        state = load(self.journal)["continuation"]
        finished = request_once(self.endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": request_id})
        evaluation = first(finished["reply"]["records"], "independent_evaluation")
        shutil.copy2(self.journal, self.root / "journal.jsonl")
        return evaluation

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        if self.process is not None:
            self.process.wait(timeout=10)
        if self.errors is not None:
            self.errors.close()
        if self.temporary is not None:
            self.temporary.cleanup()

    def __enter__(self):
        return self.start()

    def __exit__(self, *_exc):
        self.close()
