"""Independent raw-only oracle for Issue #3166 rung2; imports no runner/policy."""
from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from pathlib import Path

ROOT = Path("/evidence")
STUDY = Path("/repo/research/integration/issue_3166_gate_integrity_rung2_v1")
FREEZE = json.loads((STUDY / "FREEZE.json").read_text(encoding="utf-8"))
POLICIES = ("TWO_TIER_FRESH_GATE", "DEPENDENCY_ONLY", "GATE_ONLY", "CACHED_PREPARE_GATE")
SCENARIOS = (
    "valid", "stale_dependency_version", "fresh_false", "fresh_unknown",
    "stale_true", "lineage_mismatch", "missing_lineage", "malformed_timestamp",
    "cross_intent", "cross_epoch",
)
errors: list[str] = []
checks: list[dict] = []


def check(name: str, passed: bool, detail=None) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})
    if not passed:
        errors.append(name)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dependency_ok(prepared: dict, current: dict) -> bool:
    return (
        type(prepared.get("dependency_version")) is int
        and type(current.get("dependency_version")) is int
        and prepared["dependency_version"] == current["dependency_version"]
        and type(prepared.get("observation_generation")) is int
        and type(current.get("observation_generation")) is int
        and prepared["observation_generation"] == current["observation_generation"]
    )


def receipt_ok(prepared: dict, receipt: object, upper_ns: int) -> bool:
    if type(receipt) is not dict:
        return False
    fields = {"schema", "source_id", "target_id", "lineage", "truth",
              "issued_at_ns", "intent_id", "commit_epoch"}
    if set(receipt) != fields or receipt.get("schema") != "fixture-commit-gate-v1":
        return False
    if any(type(receipt.get(key)) is not str or not receipt[key]
           for key in ("source_id", "target_id", "lineage", "intent_id")):
        return False
    if receipt.get("truth") is not True or type(receipt.get("issued_at_ns")) is not int:
        return False
    if type(receipt.get("commit_epoch")) is not int:
        return False
    if any(receipt[key] != prepared.get(key) for key in
           ("source_id", "target_id", "lineage", "intent_id", "commit_epoch")):
        return False
    prepared_ns = prepared.get("prepared_at_ns")
    issued = receipt["issued_at_ns"]
    return (type(prepared_ns) is int and prepared_ns <= issued <= upper_ns
            and upper_ns - issued <= 15_000_000_000)


def expected(policy: str, prepared: dict, current: dict, receipt: object, now_ns: int) -> bool:
    dep = dependency_ok(prepared, current)
    gate = receipt_ok(prepared, receipt, now_ns)
    if policy == "TWO_TIER_FRESH_GATE":
        return dep and gate
    if policy == "DEPENDENCY_ONLY":
        return dep
    if policy == "GATE_ONLY":
        return gate
    if policy == "CACHED_PREPARE_GATE":
        return dep and prepared.get("cached_prepare_gate") is True
    raise AssertionError(policy)


try:
    raw_path = ROOT / "raw.jsonl"
    raw_lines = raw_path.read_bytes().splitlines()
    records = [json.loads(line) for line in raw_lines]
    source_hashes = json.loads((ROOT / "source_hashes.json").read_text(encoding="utf-8"))
    expected_hashes = FREEZE["source_sha256"]
    recomputed = {name: sha(Path("/repo") / name) for name in expected_hashes}
    check("source_hashes_equal_freeze", source_hashes == expected_hashes == recomputed)
    check("expected_raw_record_count_43", len(records) == 43, len(records))
    check("jsonl_no_blank_or_duplicate_bytes", len(raw_lines) == 43 and all(raw_lines))

    matrix = [row for row in records if row.get("record_type") == "matrix"]
    duplicate = [row for row in records if row.get("record_type") == "duplicate_attempt"]
    contradictory = [row for row in records if row.get("record_type") == "contradictory_control"]
    keys = [(row.get("case"), row.get("policy")) for row in matrix]
    expected_keys = [(scenario, policy) for scenario in SCENARIOS for policy in POLICIES]
    check("all_40_matrix_cells_exactly_once", len(matrix) == 40 and
          Counter(keys) == Counter(expected_keys), {"rows": len(matrix), "duplicates":
          [key for key, n in Counter(keys).items() if n != 1]})
    check("two_duplicate_attempt_records", len(duplicate) == 2 and
          sorted(row.get("attempt") for row in duplicate) == [1, 2])
    check("one_contradictory_control", len(contradictory) == 1)

    for row in matrix:
        key = f"{row.get('case')}::{row.get('policy')}"
        start, end = row.get("started_ns"), row.get("ended_ns")
        valid_times = type(start) is int and type(end) is int and start <= end
        check(f"{key}:well_formed_time", valid_times)
        expected_admission = expected(row["policy"], row["prepared"], row["current"],
                                      row["gate_receipt"], end if valid_times else 0)
        check(f"{key}:admission_recomputed", row.get("admitted") is expected_admission,
              {"observed": row.get("admitted"), "expected": expected_admission})
        check(f"{key}:target_remained_live", row.get("target_live_before_admission") is True
              and row.get("current", {}).get("target_live") is True)
        if not expected_admission:
            check(f"{key}:refusal_zero_side_effect", row.get("runtime_called") is False
                  and row.get("dispatch") is None and row.get("emissions") == 0
                  and row.get("effect") is None and row.get("events") == [])
        else:
            check(f"{key}:runtime_called", row.get("runtime_called") is True)
            check(f"{key}:native_complete_release", row.get("native_status") == "completed"
                  and row.get("release_verified") is True and row.get("emissions", 0) > 0)
            check(f"{key}:exact_effect", row.get("effect") == {"saved": True, "text": ""}
                  and row.get("postcondition_exact") is True)
            check(f"{key}:one_save_event", sum(e.get("type") == "save"
                  for e in row.get("events", [])) == 1)
        cleanup = row.get("fixture_cleanup", {})
        check(f"{key}:cleanup", cleanup.get("exit_code") == 0 and cleanup.get("error") is None)

    invalid_two_tier = [r for r in matrix if r["policy"] == "TWO_TIER_FRESH_GATE"
                        and r["case"] != "valid" and r.get("admitted")]
    check("two_tier_no_invalid_admission", not invalid_two_tier,
          [f"{r['case']}:{r['emissions']}" for r in invalid_two_tier])
    for policy in POLICIES[1:]:
        witnesses = [r for r in matrix if r["policy"] == policy and r["case"] != "valid"
                     and r.get("admitted") is True and r.get("postcondition_exact") is True]
        check(f"{policy}:unsafe_effect_witness", bool(witnesses), len(witnesses))

    duplicate_probe_ids = {row.get("probe_id") for row in duplicate}
    duplicate_programs = [row.get("program") for row in duplicate]
    same_program = (len(duplicate_programs) == 2 and
                    duplicate_programs[0] == duplicate_programs[1])
    same_receipt = len(duplicate) == 2 and duplicate[0].get("receipt") == duplicate[1].get("receipt")
    check("duplicate_same_probe_program_and_receipt", len(duplicate_probe_ids) == 1
          and same_program and same_receipt)
    duplicate_save_counts = [sum(event.get("type") == "save" for event in row.get("events", []))
                             for row in sorted(duplicate, key=lambda item: item.get("attempt", 0))]
    duplicate_saves = max(duplicate_save_counts, default=0)
    duplicate_replay_accepted = (len(duplicate) == 2 and duplicate[1].get("admitted") is True
                                 and duplicate[1].get("native_status") == "completed"
                                 and duplicate_save_counts == [1, 2])
    check("duplicate_effect_count_retained", duplicate_save_counts in ([1, 1], [1, 2]),
          duplicate_save_counts)
    check("duplicate_disposition_matches_raw",
          all(row.get("probe_disposition") == ("FAIL_DUPLICATE_COMMIT_REPLAY_ACCEPTED"
              if duplicate_replay_accepted else "DUPLICATE_COMMIT_REFUSED_SCOPED") for row in duplicate))
    check("duplicate_cleanup", all(row.get("fixture_cleanup", {}).get("exit_code") == 0
          and row.get("fixture_cleanup", {}).get("error") is None for row in duplicate))

    control = contradictory[0] if contradictory else {}
    partial_effect = {"saved": True, "text": "", "collateral": "fixture-label"}
    check("contradictory_control_not_exact_success", control.get("effect") == partial_effect
          and control.get("postcondition_exact") is False
          and control.get("disposition") == "HOLD_POSTCONDITION_CONTRADICTORY"
          and control.get("native_status") == "completed"
          and control.get("dispatch", {}).get("task_success") is None)
    check("contradictory_control_cleanup",
          control.get("fixture_cleanup", {}).get("exit_code") == 0
          and control.get("fixture_cleanup", {}).get("error") is None)

    expected_formal_pass = not invalid_two_tier and not duplicate_replay_accepted
    report = {
        "schema": "issue3166-rung2-independent-audit-v1",
        "allocation": FREEZE["allocation"],
        "source_commit": FREEZE["source_commit"],
        "records": len(records),
        "matrix_rows": len(matrix),
        "duplicate_attempts": len(duplicate),
        "contradictory_controls": len(contradictory),
        "raw_sha256": sha(raw_path),
        "check_count": len(checks),
        "errors": errors,
        "checks": checks,
        "duplicate_replay_accepted": duplicate_replay_accepted,
        "formal_finding": "PASS_GATE_INTEGRITY_RUNG2_SCOPED" if expected_formal_pass
            else "FAIL_GATE_INTEGRITY_RUNG2",
        "audit_disposition": "PASS_RAW_AUDIT" if not errors else "HOLD_RAW_AUDIT_ERRORS",
        "scope": "GTK/Xvfb fixture and frozen evidence comparators only; not a production gate API",
        "audited_at_utc_ns": time.time_ns(),
    }
except Exception as exc:
    report = {"schema": "issue3166-rung2-independent-audit-v1",
              "audit_disposition": "HOLD_RAW_AUDIT_ERRORS",
              "errors": [f"auditor_exception:{type(exc).__name__}:{exc}"],
              "checks": checks}

out = ROOT / "AUDIT.json"
out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: report.get(key) for key in
                  ("audit_disposition", "formal_finding", "records", "check_count", "errors",
                   "duplicate_replay_accepted", "raw_sha256")}, sort_keys=True))
raise SystemExit(0 if report.get("audit_disposition") == "PASS_RAW_AUDIT" else 2)
