#!/usr/bin/env python3
"""One-shot newline-framing boundary experiment for Issue #3814."""
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


BASE_COMMIT = "c215b11fc9609ec02810a22317c926374f399858"
SOURCE_ROOTS = ("runtime/cli_v1", "runtime/motor_state_v1", "runtime/selector_v1")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_digests(root):
    rows = []
    for relative in SOURCE_ROOTS:
        for path in sorted((root / relative).rglob("*.py")):
            data = path.read_bytes()
            canonical = data.replace(b"\r\n", b"\n")
            rows.append({"path": path.relative_to(root).as_posix(),
                         "sha256": sha(canonical), "bytes": len(canonical),
                         "runtime_sha256": sha(data), "runtime_bytes": len(data)})
    return rows


class Relay:
    def __init__(self, limit=None):
        self.accepted = bytearray()
        self.limit = limit

    def write(self, text):
        self.accepted.extend(text.encode("utf-8"))
        return len(text)

    def flush(self):
        pass

    def delivery(self):
        accepted = bytes(self.accepted)
        return accepted if self.limit is None else accepted[:self.limit]


def call_cli(argv, dispatch_result, calls, stdout):
    old_argv, old_stdout = sys.argv, sys.stdout

    def dispatch(**kwargs):
        calls.append(kwargs)
        return dispatch_result

    sys.argv, sys.stdout = ["agent-interface", *argv], stdout
    try:
        with patch.object(cli, "dispatch", side_effect=dispatch):
            code = cli.main()
    finally:
        sys.argv, sys.stdout = old_argv, old_stdout
    return code, stdout.getvalue()


def snapshot(root):
    rows = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": sha(data)})
    return rows


def invoke(argv, synthetic, calls, relay):
    old_argv, old_stdout = sys.argv, sys.stdout

    def dispatch(**kwargs):
        calls.append(kwargs)
        return synthetic

    sys.argv, sys.stdout = ["agent-interface", *argv], relay
    try:
        with patch.object(cli, "dispatch", side_effect=dispatch):
            code = cli.main()
    finally:
        sys.argv, sys.stdout = old_argv, old_stdout
    return code


def main():
    root = Path("/source").resolve()
    out = Path(os.environ.get("OUT", "/out")).resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_FRESH_EMPTY")
    if os.environ.get("EXPECTED_COMMIT") != BASE_COMMIT:
        raise SystemExit("STOP_BASE_COMMIT_MISMATCH")

    source_manifest = source_digests(root)
    sources = {row["path"]: row["sha256"] for row in source_manifest}
    runner_sha = sha((root / "research/experiments/issue_3814_newline_frame_v1/runner.py").read_bytes())
    auditor_sha = sha((root / "research/experiments/issue_3814_newline_frame_v1/audit.py").read_bytes())
    image_ref = os.environ.get("IMAGE_REF", "")
    if not image_ref.endswith("44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b"):
        raise SystemExit("STOP_IMAGE_REF_MISMATCH")

    synthetic = {
        "schema": "agent-interface/runtime-dispatch-result-v1",
        "status": "returned",
        "result": {"status": "completed", "effect_status": "synthetic_only",
                   "execution": {"emissions": 0, "input_release_verified": True}},
    }
    rows = []
    with tempfile.TemporaryDirectory(prefix="issue3814-") as temporary:
        root_tmp = Path(temporary)
        program, targets = root_tmp / "program.json", root_tmp / "targets.json"
        program.write_text('{"ops":[]}', encoding="utf-8")
        targets.write_text('{"fixture":1}', encoding="utf-8")
        common = ["dispatch", "--program", str(program), "--targets", str(targets),
                  "--current-observation-seq", "1", "--current-binding-revision", "0"]

        # Complete-delivery control.
        full_dir, calls, relay = root_tmp / "complete", [], Relay()
        code = invoke([*common, "--run-directory", str(full_dir)], synthetic, calls, relay)
        accepted_full, delivered_full = bytes(relay.accepted), relay.delivery()
        parsed_full = json.loads(delivered_full)
        if (code != 0 or accepted_full != delivered_full or not delivered_full.endswith(b"\n")
                or parsed_full.get("result", {}).get("status") != "completed" or len(calls) != 1):
            raise AssertionError("complete_delivery_control_failed")
        rows.append({"case": "complete_delivery", "producer_exit": code,
                     "accepted_b64": base64.b64encode(accepted_full).decode("ascii"),
                     "delivered_b64": base64.b64encode(delivered_full).decode("ascii"),
                     "dispatch_calls": len(calls), "terminal_lf": delivered_full.endswith(b"\n"),
                     "parsed_status": parsed_full["result"]["status"], "files": snapshot(full_dir)})

        # Exactly one terminal LF is lost downstream; all producer bytes were accepted.
        run_dir, calls, relay = root_tmp / "newline_lost", [], Relay()
        code = invoke([*common, "--run-directory", str(run_dir)], synthetic, calls, relay)
        accepted, delivered = bytes(relay.accepted), relay.delivery()
        if code != 0 or not accepted.endswith(b"\n") or len(accepted) < 2:
            raise AssertionError("producer_full_acceptance_failed")
        relay.limit = len(accepted) - 1
        delivered = relay.delivery()
        if delivered != accepted[:-1] or delivered.endswith(b"\n"):
            raise AssertionError("not_exact_terminal_lf_prefix")

        # Parser-only caller demonstration: valid JSON despite strict-prefix delivery.
        naive = json.loads(delivered)
        naive_claims_completed = naive.get("result", {}).get("status") == "completed"
        frame_valid = delivered.endswith(b"\n")

        before = snapshot(run_dir)
        status_out, status_calls = io.StringIO(), []
        status_code, status_text = call_cli(
            ["attempt-status", "--run-directory", str(run_dir)], None, status_calls, status_out)
        status = json.loads(status_text)
        review_out, review_calls = io.StringIO(), []
        review_code, review_text = call_cli(
            ["review", "--report", str(run_dir / "report.json"), "--run-directory", str(run_dir)],
            None, review_calls, review_out)
        reviewed = json.loads(review_text)
        after = snapshot(run_dir)
        report_bytes = (run_dir / "report.json").read_bytes()
        report = json.loads(report_bytes)
        status_report = status.get("files", {}).get("report.json", {})
        review_report = reviewed.get("receipt", {}).get("report", {})
        review_report_sha = reviewed.get("receipt", {}).get("source", {}).get("sha256")
        guard_and_recovery = (
            not frame_valid and naive_claims_completed and code == 0 and len(accepted) > len(delivered)
            and accepted.startswith(delivered) and delivered == accepted[:-1]
            and status_code == 0 and status.get("status") == "report_recorded"
            and status.get("replay_allowed") is False and status_report.get("state") == "recorded"
            and status_report.get("sha256") == sha(report_bytes) and status_report.get("value") == report
            and review_code == 0 and review_report == report and review_report_sha == sha(report_bytes)
            and reviewed.get("outcome_summary", {}).get("execution_status") == "completed"
            and before == after and len(calls) == 1 and not status_calls and not review_calls
        )
        if not guard_and_recovery:
            raise AssertionError("framing_guard_or_read_only_recovery_failed")
        rows.append({"case": "terminal_lf_lost", "producer_exit": code,
                     "accepted_b64": base64.b64encode(accepted).decode("ascii"),
                     "accepted_sha256": sha(accepted), "delivered_b64": base64.b64encode(delivered).decode("ascii"),
                     "delivered_sha256": sha(delivered), "naive_parse": "valid_json",
                     "naive_claims_completed": naive_claims_completed, "frame_valid": frame_valid,
                     "frame_guard": "reject_missing_terminal_lf", "dispatch_calls": len(calls),
                     "attempt_status_exit": status_code, "attempt_status": status,
                     "review_exit": review_code, "review": reviewed,
                     "report_b64": base64.b64encode(report_bytes).decode("ascii"),
                     "report_sha256": sha(report_bytes), "snapshot_before": before,
                     "snapshot_after": after, "guard_and_recovery_pass": guard_and_recovery})

        # Request-only status must stay unknown and never attempt dispatch.
        unknown_dir = root_tmp / "request_only"
        unknown_dir.mkdir()
        request = {"schema": "agent-interface/cli-attempt-v1", "operation": "dispatch",
                   "arguments": {"program": {"ops": []}}}
        (unknown_dir / "request.json").write_text(json.dumps(request), encoding="utf-8")
        unknown_out, unknown_calls = io.StringIO(), []
        unknown_code, unknown_text = call_cli(
            ["attempt-status", "--run-directory", str(unknown_dir)], None, unknown_calls, unknown_out)
        unknown = json.loads(unknown_text)
        if (unknown_code != 2 or unknown.get("status") != "unknown_or_incomplete"
                or unknown.get("replay_allowed") is not False or unknown_calls):
            raise AssertionError("request_only_control_failed")
        rows.append({"case": "request_only_unknown", "attempt_status_exit": unknown_code,
                     "attempt_status": unknown, "dispatch_calls": len(unknown_calls),
                     "files": snapshot(unknown_dir)})

        # Existing directory refuses before the synthetic dispatch facade.
        occupied = root_tmp / "occupied"
        occupied.mkdir()
        (occupied / "sentinel").write_bytes(b"preserve-me")
        occupied_calls, occupied_out = [], Relay()
        occupied_code = invoke([*common, "--run-directory", str(occupied)], synthetic, occupied_calls, occupied_out)
        refusal = json.loads(occupied_out.delivery())
        if (occupied_code != 2 or occupied_calls or refusal.get("error") != "REQUEST_PERSISTENCE_FAILED"
                or (occupied / "sentinel").read_bytes() != b"preserve-me"):
            raise AssertionError("occupied_destination_control_failed")
        rows.append({"case": "occupied_destination", "producer_exit": occupied_code,
                     "response": refusal, "dispatch_calls": len(occupied_calls),
                     "files": snapshot(occupied)})

    raw_doc = {
        "schema": "issue-3814/newline-frame-raw-v1", "base_commit": BASE_COMMIT,
        "image_ref": image_ref, "container_platform": "linux/amd64",
        "source_sha256": source_manifest, "runner_sha256": runner_sha,
        "auditor_sha256": auditor_sha, "rows": rows,
        "formal_decision": "FAIL_FALSE_SUCCESS",
        "secondary_decision": "PASS_FRAMING_GUARD_RECOVERY_SCOPED",
    }
    raw = json.dumps(raw_doc, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    (out / "raw.json").write_bytes(raw)
    print(json.dumps({"formal_decision": raw_doc["formal_decision"],
                      "secondary_decision": raw_doc["secondary_decision"],
                      "rows": len(rows), "raw_sha256": sha(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
