"""Read-only audit of the R16 freeze, custody, recovery, and raw manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(root: Path, manifest: Path):
    errors = []
    entries = 0
    if not manifest.is_file():
        return {"present": False, "entries": 0, "errors": ["manifest missing"]}
    for number, line in enumerate(manifest.read_text(encoding="ascii").splitlines(), 1):
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
            path = (root / relative).resolve()
            path.relative_to(root.resolve())
            if not path.is_file():
                errors.append(f"line {number}: missing {relative}")
            elif sha(path) != expected:
                errors.append(f"line {number}: hash mismatch {relative}")
            entries += 1
        except Exception as error:
            errors.append(f"line {number}: {type(error).__name__}: {error}")
    return {"present": True, "entries": entries, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretrial-only", action="store_true")
    args = parser.parse_args()
    conditions = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
    checks = {}
    source = ROOT / conditions["source_evidence"]["result"]
    checks["source_result_sha256"] = source.is_file() and sha(source) == conditions[
        "source_evidence"]["result_sha256"]
    source_result = json.loads(source.read_text(encoding="utf-8")) if source.is_file() else {}
    source_report = source_result.get("dispatch_terminal", {}).get("receipt", {}).get("report", {})
    checks["source_operation_and_generation"] = (
        source_report.get("operation_id") == conditions["source_evidence"]["operation_id"]
        and source_report.get("supervision", {}).get("action", {}).get("target_generation")
            == conditions["source_evidence"]["target_generation"])
    checks["source_unknown_fields_preserved"] = (
        source_report.get("input_dispatched") is None
        and source_report.get("result", {}).get("task_success") is None
        and source_report.get("replay_allowed") is False
        and source_result.get("retained_result", {}).get("cancellation", {}).get(
            "result", {}).get("late_input_horizon_verified") is False)
    pretrial = check_manifest(ROOT, PACKET / "PRETRIAL_SHA256SUMS")
    checks["pretrial_manifest"] = pretrial["present"] and not pretrial["errors"]
    if args.pretrial_only:
        report = {"audit": "R16_PRETRIAL", "checks": checks,
            "manifest": pretrial,
            "pass": all(checks.values())}
    else:
        run = PACKET / "run"
        raw = check_manifest(run, run / "SHA256SUMS")
        checks["raw_manifest"] = raw["present"] and not raw["errors"]
        result_path = run / "result.json"
        checks["result_present"] = result_path.is_file()
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {}
        checks["exactly_one_recovery_call"] = result.get("public_recovery_attempt_count") == 1
        checks["no_task_dispatch"] = result.get("task_dispatch_attempted") is False
        checks["fence_preimage_exact"] = result.get("fence_before", {}).get("sha256") == conditions[
            "persistent_fence"]["expected_sha256_before"]
        if result.get("classification") == "PASS_SCOPED_ORPHAN_RECOVERY_WITH_HORIZON":
            checks["all_acceptance_checks"] = bool(result.get("acceptance_checks")) and all(
                value is True for value in result["acceptance_checks"].values())
        else:
            checks["all_acceptance_checks"] = False
        report = {"audit": "R16_POSTTRIAL", "classification": result.get("classification"),
            "checks": checks, "raw_manifest": raw,
            "acceptance_checks": result.get("acceptance_checks", {}),
            "pass": all(checks.values())}
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
