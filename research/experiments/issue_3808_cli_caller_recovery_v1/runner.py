#!/usr/bin/env python3
"""One-shot synthetic caller-boundary experiment for Issue #3808."""
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

from runtime.cli_v1 import __main__ as cli
from runtime.cli_v1.attempt import inspect_attempt


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Relay:
    def __init__(self, delivered_limit=None):
        self.accepted = bytearray()
        self.delivered_limit = delivered_limit

    def write(self, text):
        data = text.encode("utf-8")
        self.accepted.extend(data)
        return len(text)

    def flush(self):
        pass

    def delivered(self):
        data = bytes(self.accepted)
        return data if self.delivered_limit is None else data[:self.delivered_limit]


def invoke_cli(argv, dispatch_result, dispatch_calls, relay=None):
    if relay is None:
        relay = io.StringIO()
    original_argv, original_stdout = sys.argv, sys.stdout
    sys.argv, sys.stdout = ["agent-interface", *argv], relay
    try:
        with patch.object(cli, "dispatch", side_effect=lambda **kwargs: (dispatch_calls.append(kwargs), dispatch_result)[1]):
            code = cli.main()
    finally:
        sys.argv, sys.stdout = original_argv, original_stdout
    value = relay.getvalue() if isinstance(relay, io.StringIO) else relay.delivered().decode("utf-8", errors="replace")
    return code, value, relay


def snapshot(root):
    rows = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            raw = path.read_bytes()
            rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(raw), "sha256": digest(raw)})
    return rows


def main():
    out = Path(os.environ.get("OUT", "/out")).resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_FRESH_EMPTY")
    result = {"schema": "issue-3808/caller-recovery-raw-v1", "base_commit": "ddb311528e96e2a613dd660f8cb24b14f413081d", "rows": []}
    completed = {"schema": "agent-interface/runtime-dispatch-result-v1", "status": "returned",
                 "result": {"status": "completed", "execution": {"emissions": 0, "input_release_verified": True},
                            "effect_status": "synthetic_fixture_only"}}
    with tempfile.TemporaryDirectory(prefix="issue3808-") as temp:
        root = Path(temp)
        program = root / "program.json"
        targets = root / "targets.json"
        program.write_text('{"ops":[]}', encoding="utf-8")
        targets.write_text('{"fixture":1}', encoding="utf-8")
        common = ["dispatch", "--program", str(program), "--targets", str(targets),
                  "--current-observation-seq", "1", "--current-binding-revision", "0"]

        # Complete-delivery positive control.
        full_dir = root / "full"
        calls = []
        code, delivered, relay = invoke_cli([*common, "--run-directory", str(full_dir)], completed, calls)
        parsed = json.loads(delivered)
        if code != 0 or parsed.get("result", {}).get("status") != "completed" or len(calls) != 1:
            raise AssertionError("complete_delivery_control_failed")
        result["rows"].append({"case": "complete_delivery", "producer_exit": code,
                               "accepted_b64": base64.b64encode(delivered.encode()).decode(),
                               "delivered_b64": base64.b64encode(delivered.encode()).decode(),
                               "dispatch_calls": len(calls), "parsed_status": parsed["result"]["status"],
                               "files": snapshot(full_dir)})

        # Relay acknowledges every producer byte but delivers a strict prefix downstream.
        trunc_dir = root / "truncated"
        calls = []
        relay = Relay(delivered_limit=37)
        code, caller_bytes, relay = invoke_cli([*common, "--run-directory", str(trunc_dir)], completed, calls, relay)
        accepted = bytes(relay.accepted)
        delivered_bytes = relay.delivered()
        try:
            json.loads(delivered_bytes)
            caller_parse = "parsed"
        except (UnicodeDecodeError, json.JSONDecodeError):
            caller_parse = "invalid_or_incomplete"
        if code != 0 or len(accepted) <= len(delivered_bytes) or accepted[:len(delivered_bytes)] != delivered_bytes:
            raise AssertionError("producer_or_relay_gate_failed")
        before_recovery = snapshot(trunc_dir)
        status_buffer = io.StringIO()
        status_code, status_text, _ = invoke_cli(["attempt-status", "--run-directory", str(trunc_dir)], None, [], status_buffer)
        status = json.loads(status_text)
        if status_code != 0 or status.get("status") != "report_recorded" or status.get("replay_allowed") is not False:
            raise AssertionError("read_only_status_gate_failed")
        review_buffer = io.StringIO()
        review_code, review_text, _ = invoke_cli(["review", "--report", str(trunc_dir / "report.json"),
                                                  "--run-directory", str(trunc_dir)], None, [], review_buffer)
        reviewed = json.loads(review_text)
        after_recovery = snapshot(trunc_dir)
        if (review_code != 0 or reviewed.get("outcome_summary", {}).get("execution_status") != "completed"
                or len(calls) != 1 or before_recovery != after_recovery):
            raise AssertionError("read_only_review_or_no_replay_gate_failed")
        report_bytes = (trunc_dir / "report.json").read_bytes()
        result["rows"].append({"case": "downstream_truncation_recovery", "producer_exit": code,
                               "accepted_b64": base64.b64encode(accepted).decode(),
                               "accepted_sha256": digest(accepted), "delivered_b64": base64.b64encode(delivered_bytes).decode(),
                               "delivered_sha256": digest(delivered_bytes), "caller_parse": caller_parse,
                               "attempt_status_exit": status_code, "attempt_status": status,
                               "review_exit": review_code, "review": reviewed, "dispatch_calls": len(calls),
                               "report_b64": base64.b64encode(report_bytes).decode(), "report_sha256": digest(report_bytes),
                               "snapshot_before_recovery": before_recovery, "snapshot_after_recovery": after_recovery})

        # Request-only uncertainty control: no report is invented and no replay is attempted.
        unknown_dir = root / "unknown"
        unknown_dir.mkdir()
        request = {"schema": "agent-interface/cli-attempt-v1", "operation": "dispatch", "arguments": {"program": {"ops": []}}}
        (unknown_dir / "request.json").write_text(json.dumps(request), encoding="utf-8")
        status_buffer = io.StringIO()
        unknown_code, unknown_text, _ = invoke_cli(["attempt-status", "--run-directory", str(unknown_dir)], None, [], status_buffer)
        unknown = json.loads(unknown_text)
        if unknown_code != 2 or unknown.get("status") != "unknown_or_incomplete" or unknown.get("replay_allowed") is not False:
            raise AssertionError("unknown_attempt_not_fail_closed")
        result["rows"].append({"case": "request_only_unknown", "attempt_status_exit": unknown_code,
                               "attempt_status": unknown, "files": snapshot(unknown_dir)})

        # Existing destination refusal control through real CLI invoke path.
        occupied = root / "occupied"
        occupied.mkdir()
        (occupied / "sentinel").write_bytes(b"preserve-me")
        calls = []
        code, text, _ = invoke_cli([*common, "--run-directory", str(occupied)], completed, calls)
        refused = json.loads(text)
        if code != 2 or calls or refused.get("error") != "REQUEST_PERSISTENCE_FAILED":
            raise AssertionError("occupied_destination_invoked_dispatch")
        result["rows"].append({"case": "occupied_destination", "producer_exit": code,
                               "response": refused, "dispatch_calls": len(calls), "files": snapshot(occupied)})

    raw = json.dumps(result, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (out / "raw.json").write_bytes(raw)
    print(json.dumps({"decision": "PASS_CALLER_RECOVERS_AFTER_DOWNSTREAM_TRUNCATION_SCOPED",
                      "rows": len(result["rows"]), "raw_sha256": digest(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
