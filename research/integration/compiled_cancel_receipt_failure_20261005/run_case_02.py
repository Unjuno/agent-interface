#!/usr/bin/env python3
"""Run construction attempt 02 of the frozen synthetic boundary probe."""
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "sources"))
sys.path.insert(0, str(HERE / "sources/research/integration/compiled_gui_bundle_57_20261004/a06-layout-b-cropocr"))

from adapter import CompiledExecution  # noqa: E402


class FakeClient:
    def __init__(self, image, root):
        self.runtime = image.parent
        self.root = root
        self.image = image
        self.sequence = 0
        self.commands = []
        self.programs = []

    def _observation(self):
        self.sequence += 1
        return {
            "sequence": self.sequence,
            "capture_ns": time.perf_counter_ns(),
            "image": str(self.image),
            "context": "READY",
        }

    def check(self, _alias, _offset, _request_id):
        return ({"eligible": True, "status": "VALID"},
                {"observations": [self._observation()]})

    def submit(self, _name, _steps):
        return {"observations": [self._observation()]}

    def clock(self):
        return {"sequence": self.sequence, "runtime_ns": time.perf_counter_ns()}

    def call(self, payload):
        self.commands.append(payload)
        terminal = {
            "event": "terminal",
            "id": "completed-action-1",
            "status": "completed",
            "release": {"verified": True, "keys_down": [], "buttons_down": []},
        }
        now = time.perf_counter_ns()
        return {"reply": {"records": [terminal]}}, now, now


def main():
    source_image = HERE / "inputs/frame-068.png"
    checks = {"count": 0}

    def cancelled():
        checks["count"] += 1
        if checks["count"] == 4:
            raise RuntimeError("synthetic cancellation source unavailable")
        return False

    task = {"task_id": "task-4", "token": "t991028-4", "layout": "B"}
    escaped = None
    receipt = None
    with tempfile.TemporaryDirectory() as directory:
        client = FakeClient(source_image, Path(directory))
        adapter = CompiledExecution(
            client,
            task,
            {"field": "task-4-field", "submit": "task-4-submit"},
            cancelled=cancelled,
            ocr_runner=lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0, stdout="", stderr=""
            ),
        )
        try:
            receipt = adapter.run()["receipt"]
        except Exception as error:  # capture the behavior under test
            escaped = {"type": type(error).__name__, "message": str(error)}

        terminal_events = [row for row in adapter.events if row.get("event") == "action_terminal"]
        result = {
            "schema": "compiled_cancel_receipt_failure_result_v1",
            "study": "compiled-cancel-receipt-failure-20261005-02",
            "source_commit": "6144a1b0a2c88f5d88ff1fce148381f1f22269e",
            "callback_checks": checks["count"],
            "client_command_count": len(client.commands),
            "action_terminal_events": terminal_events,
            "runtime_finished_events": [row for row in adapter.events if row.get("event") == "runtime_finished"],
            "adapter_returned_receipt": receipt is not None,
            "returned_receipt": receipt,
            "escaped_exception": escaped,
            "completed_adapter_programs": [
                {"label": row["label"], "status": row["terminal"]["status"],
                 "release": row["terminal"]["release"]}
                for row in client.programs
            ],
            "fixture_sha256": hashlib.sha256(source_image.read_bytes()).hexdigest(),
            "scope": "synthetic adapter/core boundary; no GUI, game, Docker, model, or task allocation",
        }
    output = HERE / "out/attempt-02/RESULT.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
