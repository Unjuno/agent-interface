"""Independent stdlib-only auditor for Issue #3814 formal-01."""
from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(evidence: Path, freeze_path: Path, source: Path) -> dict:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    def check(condition: bool, name: str) -> None:
        checks[name] = bool(condition)
        if not condition:
            errors.append(name)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for rel, expected in freeze["source_sha256"].items():
        actual = digest((source / rel).read_bytes())
        check(actual == expected, f"SOURCE_HASH:{rel}")
    manifest = (evidence / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    listed: dict[str, str] = {}
    for line in manifest:
        sha, rel = line.split("  ", 1)
        listed[rel] = sha
        path = evidence / rel
        check(path.is_file(), f"MANIFEST_MISSING:{rel}")
        if path.is_file():
            check(digest(path.read_bytes()) == sha, f"MANIFEST_HASH:{rel}")
    actual_paths = {p.relative_to(evidence).as_posix() for p in evidence.rglob("*") if p.is_file() and p.name != "SHA256SUMS"}
    check(actual_paths == set(listed), "MANIFEST_COVERAGE")

    full = (evidence / "relay-accepted.bin").read_bytes()
    delivered = (evidence / "caller-delivered.bin").read_bytes()
    result = json.loads((evidence / "RESULT.json").read_text(encoding="utf-8"))
    expected_container = {
        "image_ref": freeze["C"]["image"], "image_id": freeze["C"]["image_id"],
        "platform": freeze["C"]["platform"], "docker_server": freeze["C"]["docker_server"],
    }
    check(result.get("container") == expected_container, "FORMAL_CONTAINER_IDENTITY")
    check(result.get("base_commit") == freeze.get("base_commit"), "FORMAL_BASE_COMMIT")
    attempt = json.loads((evidence / "attempt-status.stdout.bin").read_bytes())
    raw_receipt = json.loads((evidence / "receipt-raw.stdout.bin").read_bytes())
    review = json.loads((evidence / "review.stdout.bin").read_bytes())
    request_only = json.loads((evidence / "request-only-status.stdout.bin").read_bytes())
    preexisting = json.loads((evidence / "preexisting.stdout.bin").read_bytes())
    report_path = evidence / "work" / "attempt-formal-01" / "report.json"
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    before, after = result["attempt_file_sha256_before"], result["attempt_file_sha256_after"]
    final_snapshot = {p.relative_to(report_path.parent).as_posix(): digest(p.read_bytes())
                      for p in sorted(report_path.parent.rglob("*")) if p.is_file()}

    check(full.endswith(b"\n"), "PRODUCER_TERMINAL_LF")
    check(delivered == full[:-1] and len(full) == len(delivered) + 1, "STRICT_ONE_BYTE_PREFIX")
    parsed_prefix = json.loads(delivered)
    parser_only_false_success = (parsed_prefix.get("status") == "returned"
                                 and parsed_prefix.get("result", {}).get("status") == "completed")
    check(parser_only_false_success, "PARSER_ONLY_FALSE_SUCCESS_REPRODUCED")
    check(not delivered.endswith(b"\n"), "FRAMING_GUARD_PREDICATE")
    check(result["producer"]["returncode"] == 0 and (evidence / "producer.returncode.txt").read_text() == "0",
          "PRODUCER_EXIT")
    check(result["producer"]["stdout_sha256"] == digest(full), "PRODUCER_SHA")
    check(result["producer"]["delivered_sha256"] == digest(delivered), "DELIVERED_SHA")
    preflight = result.get("preflight", {})
    check(preflight.get("disposition") == "PASS_SOURCE_FREEZE"
          and preflight.get("source_check_count") == len(freeze["source_sha256"])
          and all(preflight.get("source_checks", {}).values()), "FORMAL_SOURCE_IMAGE_PREFLIGHT")
    check(attempt.get("status") == "report_recorded" and attempt.get("replay_allowed") is False,
          "ATTEMPT_STATUS_FAIL_CLOSED")
    check(result["recovery"]["attempt_status_returncode"] == 0
          and result["recovery"]["receipt_returncode"] == 0
          and result["recovery"]["review_returncode"] == 0, "RECOVERY_EXIT_CODES")
    check(attempt.get("files", {}).get("report.json", {}).get("value") == report,
          "ATTEMPT_REPORT_VALUE")
    check(raw_receipt == report, "RECEIPT_RAW_EXACT_REPORT")
    check(review.get("receipt", {}).get("source", {}).get("sha256") == digest(report_bytes),
          "REVIEW_REPORT_SHA")
    check(before == after == final_snapshot, "ATTEMPT_FILES_IMMUTABLE")
    check(result["recovery"]["report_bytes_unchanged"] is True, "REPORT_UNCHANGED_RECORDED")
    check(result["dispatch_facade_calls"] == 1 and (evidence / "dispatch-count.txt").read_text() == "1",
          "DISPATCH_EXACTLY_ONCE")
    check(result["controls"]["complete_delivery_pass"] is True, "COMPLETE_DELIVERY_CONTROL")
    check(request_only.get("status") == "unknown_or_incomplete" and request_only.get("replay_allowed") is False,
          "REQUEST_ONLY_UNKNOWN_NO_REPLAY")
    check(result["controls"]["request_only_returncode"] == 0
          and result["controls"]["preexisting_returncode"] != 0, "CONTROL_EXIT_CODES")
    check(result["controls"]["preexisting_facade_calls_unchanged"] is True
          and (evidence / "work" / "attempt-preexisting" / "sentinel.txt").read_bytes() == b"immutable-preexisting-bytes\n",
          "PREEXISTING_DESTINATION_UNCHANGED")
    check(preexisting.get("status") == "invalid_request" and preexisting.get("operation_invoked") is False,
          "PREEXISTING_REFUSED_BEFORE_DISPATCH")

    guard_pass = not delivered.endswith(b"\n")
    recovery_pass = (
        attempt.get("status") == "report_recorded" and attempt.get("replay_allowed") is False
        and attempt.get("files", {}).get("report.json", {}).get("value") == report
        and raw_receipt == report
        and review.get("receipt", {}).get("source", {}).get("sha256") == digest(report_bytes)
        and before == after == final_snapshot and result["dispatch_facade_calls"] == 1
    )
    if any(name.startswith(("SOURCE_HASH:", "MANIFEST_")) for name in errors):
        disposition = "STOP_SETUP"
    elif errors:
        disposition = "HOLD_EVIDENCE_INCOMPLETE"
    elif parser_only_false_success:
        disposition = "FAIL_FALSE_SUCCESS"
    elif guard_pass and recovery_pass:
        disposition = "PASS_FRAMING_GUARD_SCOPED"
    else:
        disposition = "HOLD_EVIDENCE_INCOMPLETE"
    return {
        "schema": "issue-3814-independent-audit-v1", "allocation": result.get("allocation"),
        "disposition": disposition, "parser_only_false_success": parser_only_false_success,
        "framing_guard_pass": guard_pass, "read_only_recovery_pass": recovery_pass,
        "checks": {"count": len(checks), "passed": sum(checks.values()), "results": checks, "errors": errors},
        "source_base_commit": freeze.get("base_commit"),
        "full_stdout_sha256": digest(full), "delivered_prefix_sha256": digest(delivered),
        "retained_report_sha256": digest(report_bytes),
        "dispatch_facade_calls": result.get("dispatch_facade_calls"),
        "scope": "independent byte/result audit of one synthetic CLI allocation; no real pipe/network/model/task",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("freeze", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.evidence, args.freeze, args.source)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
