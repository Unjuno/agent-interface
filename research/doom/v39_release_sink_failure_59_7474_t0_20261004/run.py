"""Invoke exact #7474 release-publication methods with three fake sinks."""
import ast
import hashlib
import json
from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "executor_v13.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
EXECUTOR = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "Executor")
METHODS = [n for n in EXECUTOR.body if isinstance(n, ast.FunctionDef) and n.name in {"_release_event", "_publish_cause_once"}]
namespace = {
    "time": time,
    "INTERRUPTION_REASONS": frozenset(("cancelled", "stop_requested", "focus_changed", "surface_changed", "expired")),
}
exec(compile(ast.Module(body=METHODS, type_ignores=[]), str(SOURCE), "exec"), namespace)


class Lease:
    def interruption_snapshot(self):
        return {"intent_token": "intent-1", "record": {
            "event": "owner_release", "reason": "cancelled", "verified": True,
            "keys_down": [], "buttons_down": [],
        }}


class Probe:
    _release_event = namespace["_release_event"]
    _publish_cause_once = namespace["_publish_cause_once"]

    def __init__(self, sink_mode):
        self.lock = threading.RLock()
        self.lease = Lease()
        self.active = ("action-1", self.lease)
        self.published_release_ids = set()
        self.sink_mode = sink_mode
        self.calls = 0
        self.accepted = []

    def emit(self, event):
        self.calls += 1
        if self.sink_mode == "fail_before_accept" and self.calls == 1:
            raise OSError("synthetic sink failed before acceptance")
        self.accepted.append(event)
        if self.sink_mode == "accept_then_raise" and self.calls == 1:
            raise OSError("synthetic sink accepted then raised")


def main():
    rows = []
    for mode in ("success", "fail_before_accept", "accept_then_raise"):
        probe = Probe(mode)
        caught = []
        for attempt in (1, 2):
            try:
                result = probe._publish_cause_once("action-1", probe.lease)
                caught.append({"attempt": attempt, "result": result, "error": None})
            except Exception as error:
                caught.append({"attempt": attempt, "result": None, "error": type(error).__name__})
        rows.append({
            "sink_mode": mode,
            "attempts": caught,
            "sink_calls": probe.calls,
            "accepted_events": probe.accepted,
            "published_release_marked": "action-1" in probe.published_release_ids,
            "delivery_unknown_events": [e for e in probe.accepted if e.get("event") == "delivery_unknown"],
            "retry_suppressed": caught[1]["result"] is None and caught[1]["error"] is None,
        })
    result = {
        "schema": "v39-release-sink-failure-t0-raw-v1",
        "source_git_blob": "7f308a0dd863af534f764f657d603b4921ba1c6a",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "runtime": "host Python AST-loaded exact methods; fake lease and sink; no WSLc/game/input",
        "rows": rows,
    }
    (ROOT / "raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "source_sha256": result["source_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
