#!/usr/bin/env python3
"""One-shot current-CLI JSONL terminal-newline recovery experiment."""

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

from runtime.cli_v1 import __main__ as cli


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def invoke(argv, dispatch_result, calls):
    old_argv, old_stdout = sys.argv, sys.stdout
    output = io.StringIO()
    sys.argv, sys.stdout = ["agent-interface", *argv], output
    try:
        with patch.object(
            cli,
            "dispatch",
            side_effect=lambda **kwargs: (calls.append(kwargs), dispatch_result)[1],
        ):
            code = cli.main()
    finally:
        sys.argv, sys.stdout = old_argv, old_stdout
    return code, output.getvalue().encode("utf-8")


def snapshot(root):
    rows = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            rows.append({"path": path.relative_to(root).as_posix(),
                         "bytes": len(data), "sha256": sha256(data)})
    return rows


def parse_state(data):
    try:
        value = json.loads(data)
        return "valid_json", value
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "invalid_json", None


def main():
    out = Path(os.environ.get("OUT", "/out")).resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_FRESH_EMPTY")

    completed = {
        "schema": "agent-interface/runtime-dispatch-result-v1",
        "status": "returned",
        "result": {"status": "completed",
                   "execution": {"emissions": 0, "input_release_verified": True},
                   "effect_status": "synthetic_fixture_only"},
    }
    raw = {"allocation": "issue-3834-jsonl-terminal-lf-orbstack-v1",
           "base_commit": "c215b11fc9609ec02810a22317c926374f399858", "rows": []}

    with tempfile.TemporaryDirectory(prefix="issue3834-") as temp:
        root = Path(temp)
        program, targets = root / "program.json", root / "targets.json"
        program.write_text('{"ops":[]}', encoding="utf-8")
        targets.write_text('{"fixture":1}', encoding="utf-8")
        common = ["dispatch", "--program", str(program), "--targets", str(targets),
                  "--current-observation-seq", "1", "--current-binding-revision", "0"]

        full_dir = root / "complete"
        calls = []
        code, accepted = invoke([*common, "--run-directory", str(full_dir)], completed, calls)
        state, value = parse_state(accepted[:-1] if accepted.endswith(b"\n") else accepted)
        if code != 0 or not accepted.endswith(b"\n") or state != "valid_json" or len(calls) != 1:
            raise AssertionError("complete_delivery_control_failed")
        raw["rows"].append({"case": "complete_delivery", "producer_exit": code,
                            "accepted_b64": base64.b64encode(accepted).decode(),
                            "accepted_sha256": sha256(accepted), "delivered_b64": base64.b64encode(accepted).decode(),
                            "delivered_sha256": sha256(accepted), "dispatch_calls": len(calls),
                            "json_status": state, "parsed_result_status": value["result"]["status"],
                            "files": snapshot(full_dir)})

        framing_dir = root / "terminal_lf_removed"
        calls = []
        code, accepted = invoke([*common, "--run-directory", str(framing_dir)], completed, calls)
        delivered = accepted[:-1]
        parser_state, parsed = parse_state(delivered)
        framing_complete = delivered.endswith(b"\n") and parser_state == "valid_json"
        before = snapshot(framing_dir)
        status_code, status_bytes = invoke(["attempt-status", "--run-directory", str(framing_dir)], None, [])
        status_state, status = parse_state(status_bytes)
        report_path = framing_dir / "report.json"
        review_code, review_bytes = invoke(["review", "--report", str(report_path),
                                            "--run-directory", str(framing_dir)], None, [])
        review_state, reviewed = parse_state(review_bytes)
        after = snapshot(framing_dir)
        report = report_path.read_bytes()
        if (code != 0 or not accepted.endswith(b"\n") or delivered != accepted[:-1]
                or parser_state != "valid_json" or parsed["result"]["status"] != "completed"
                or framing_complete or len(calls) != 1 or status_code != 0
                or status_state != "valid_json" or status.get("replay_allowed") is not False
                or review_code != 0 or review_state != "valid_json"
                or reviewed.get("outcome_summary", {}).get("execution_status") != "completed"
                or before != after):
            raise AssertionError("terminal_lf_recovery_gate_failed")
        raw["rows"].append({"case": "terminal_lf_removed", "producer_exit": code,
                            "accepted_b64": base64.b64encode(accepted).decode(),
                            "accepted_sha256": sha256(accepted), "delivered_b64": base64.b64encode(delivered).decode(),
                            "delivered_sha256": sha256(delivered), "removed_bytes": 1,
                            "parser_only": "valid_json_false_completion_risk",
                            "framing_aware_complete": framing_complete,
                            "parsed_status": parsed["result"]["status"],
                            "attempt_status_exit": status_code, "attempt_status": status,
                            "review_exit": review_code, "review": reviewed, "dispatch_calls": len(calls),
                            "report_b64": base64.b64encode(report).decode(), "report_sha256": sha256(report),
                            "snapshot_before": before, "snapshot_after": after})

        invalid_dir = root / "invalid_prefix"
        calls = []
        invalid_code, invalid_accepted = invoke([*common, "--run-directory", str(invalid_dir)], completed, calls)
        invalid_prefix = invalid_accepted[:max(1, len(invalid_accepted) // 2)]
        invalid_state, _ = parse_state(invalid_prefix)
        if invalid_code != 0 or invalid_state != "invalid_json" or len(calls) != 1:
            raise AssertionError("invalid_prefix_control_failed")
        raw["rows"].append({"case": "invalid_prefix", "producer_exit": invalid_code,
                            "accepted_sha256": sha256(invalid_accepted),
                            "delivered_b64": base64.b64encode(invalid_prefix).decode(),
                            "delivered_sha256": sha256(invalid_prefix), "json_status": invalid_state,
                            "dispatch_calls": len(calls)})

        unknown = root / "unknown"
        unknown.mkdir()
        request = {"schema": "agent-interface/cli-attempt-v1", "operation": "dispatch",
                   "arguments": {"program": {"ops": []}}}
        (unknown / "request.json").write_text(json.dumps(request), encoding="utf-8")
        unknown_code, unknown_bytes = invoke(["attempt-status", "--run-directory", str(unknown)], None, [])
        unknown_state, unknown_value = parse_state(unknown_bytes)
        if (unknown_code != 2 or unknown_state != "valid_json"
                or unknown_value.get("status") != "unknown_or_incomplete"
                or unknown_value.get("replay_allowed") is not False):
            raise AssertionError("request_only_control_failed")
        raw["rows"].append({"case": "request_only_unknown", "status_exit": unknown_code,
                            "status": unknown_value, "files": snapshot(unknown)})

        occupied = root / "occupied"
        occupied.mkdir()
        (occupied / "sentinel").write_bytes(b"preserve-me")
        calls = []
        occupied_code, occupied_bytes = invoke([*common, "--run-directory", str(occupied)], completed, calls)
        occupied_state, occupied_value = parse_state(occupied_bytes)
        if (occupied_code != 2 or occupied_state != "valid_json" or calls
                or occupied_value.get("error") != "REQUEST_PERSISTENCE_FAILED"):
            raise AssertionError("occupied_destination_control_failed")
        raw["rows"].append({"case": "occupied_destination", "exit": occupied_code,
                            "response": occupied_value, "dispatch_calls": len(calls),
                            "files": snapshot(occupied)})

    raw_bytes = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (out / "raw.json").write_bytes(raw_bytes)
    print(json.dumps({"decision": "PASS_FRAMING_GUARD_SCOPED", "rows": len(raw["rows"]),
                      "raw_sha256": sha256(raw_bytes)}, sort_keys=True))


if __name__ == "__main__":
    main()
