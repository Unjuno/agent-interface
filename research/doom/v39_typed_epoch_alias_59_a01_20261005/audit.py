#!/usr/bin/env python3
"""Independent raw-only reconstruction; imports neither candidate nor source."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    source_map = json.loads((ROOT / "SOURCE_MAP.json").read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    checks = {}
    for rel, expected in freeze["source_sha256"].items():
        checks[f"source_hash:{rel}"] = sha(ROOT / "source" / rel) == expected
        checks[f"source_map:{rel}"] = source_map["source_files"][rel]["sha256"] == expected
    cases = fixture["cases"]
    rows = result["cases"]
    checks["case_count"] = len(cases) == len(rows) == 9
    expected_source_acceptance = []
    expected_strict_acceptance = []
    for case, row in zip(cases, rows):
        checks[f"case_name:{case['name']}"] = row.get("name") == case["name"]
        expected_rows = {}
        strict_rows_ok = True
        source_rows_ok = True
        for signal_id in ("health", "ammo"):
            seq, capture = fixture["metadata"]["sequence"], fixture["metadata"]["capture_ns"]
            if case.get("signal") == signal_id and case.get("field") == "sequence":
                seq = case["value"]
            if case.get("signal") == signal_id and case.get("field") == "capture_ns":
                capture = case["value"]
            expected_rows[signal_id] = {"sequence": seq, "capture_ns": capture}
            source_rows_ok = source_rows_ok and seq == fixture["metadata"]["sequence"] and capture == fixture["metadata"]["capture_ns"]
            strict_rows_ok = strict_rows_ok and type(seq) is int and seq == fixture["metadata"]["sequence"] and type(capture) is int and capture == fixture["metadata"]["capture_ns"]
        expected_source_acceptance.append(source_rows_ok)
        expected_strict_acceptance.append(strict_rows_ok)
        checks[f"raw_fields:{case['name']}"] = row.get("raw_signal_fields") == expected_rows
        checks[f"actual_pipeline:{case['name']}"] = row.get("accepted") is source_rows_ok
        checks[f"strict_contract:{case['name']}"] = strict_rows_ok == (case["name"] == "control_exact_integer_epoch")
        if source_rows_ok:
            snap = row.get("snapshot")
            checks[f"snapshot_identity:{case['name']}"] = (
                type(snap) is dict and snap.get("sequence") == fixture["metadata"]["sequence"] and
                snap.get("capture_ns") == fixture["metadata"]["capture_ns"] and
                set(snap.get("signals", {})) == {"health", "ammo"})
        else:
            checks[f"rejection:{case['name']}"] = row.get("stage") == "rejected" and row.get("snapshot") is None
    alias_actual = sum(expected_source_acceptance[1:])
    checks["summary_control"] = result.get("control_accepted") is expected_source_acceptance[0]
    checks["summary_alias_count"] = result.get("malformed_aliases_accepted") == alias_actual
    checks["summary_classification"] = result.get("classification") == (
        "FAIL_CLOSED_EPOCH_IDENTITY_GAP" if expected_source_acceptance[0] and alias_actual
        else "PASS_EXACT_EPOCH_TYPE_GATE")
    audit = {"format": "issue59-v39-typed-epoch-alias-audit-v1",
             "classification": "PASS_AUDIT_RECONSTRUCTS_SOURCE_FAIL_OPEN" if all(checks.values()) and alias_actual else "FAIL_AUDIT",
             "checks_passed": sum(checks.values()), "checks_total": len(checks),
             "actual_alias_acceptances": alias_actual, "checks": checks}
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"classification": audit["classification"],
                      "checks_passed": audit["checks_passed"],
                      "checks_total": audit["checks_total"],
                      "actual_alias_acceptances": alias_actual}, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
