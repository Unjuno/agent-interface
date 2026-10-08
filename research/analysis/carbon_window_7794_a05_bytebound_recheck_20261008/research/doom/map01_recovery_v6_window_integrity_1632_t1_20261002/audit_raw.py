"""Independent, raw-only arithmetic check for v6 planner-window summaries."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

PHASE = "immediately_after_delay_before_fallback_cleanup"
ARMS = ("coast_control", "bounded_recovery")
PAIRS = (1, 2, 3)


def row_errors(row: dict) -> list[str]:
    errors = []
    pair, arm = row.get("pair_index"), row.get("arm")
    tag = f"pair{pair}:{arm}"
    window = row.get("planner_window")
    if type(window) is not dict:
        return [f"{tag}:planner_window_missing"]
    if window.get("end_boundary_phase") != PHASE:
        errors.append(f"{tag}:planner_end_phase")
    start, end, duration = (
        window.get("start_ns"), window.get("end_ns"), window.get("duration_ns")
    )
    if any(type(value) is not int for value in (start, end, duration)):
        errors.append(f"{tag}:planner_window_integer_fields")
    elif end <= start:
        errors.append(f"{tag}:planner_window_nonpositive")
    elif duration != end - start:
        errors.append(f"{tag}:planner_window_duration_mismatch")
    return errors


def inspect(payload: dict) -> dict:
    rows = payload.get("arm_summaries")
    failures = []
    if type(rows) is not list or len(rows) != 6:
        failures.append("arm_summary_count")
        rows = rows if type(rows) is list else []
    keys = [(row.get("pair_index"), row.get("arm")) for row in rows
            if type(row) is dict]
    expected = {(pair, arm) for pair in PAIRS for arm in ARMS}
    if len(keys) != 6 or set(keys) != expected:
        failures.append("arm_summary_identity")
    for row in rows:
        if type(row) is not dict:
            failures.append("arm_summary_not_object")
            continue
        failures.extend(row_errors(row))

    v6 = payload.get("v6_audit_clean")
    expected_v6 = {
        "decision": "PASS_MECHANISM_ONLY",
        "valid_experiment": True,
        "promotable_mechanism_result": True,
        "planner_boundary_failures": [],
    }
    if type(v6) is not dict or any(v6.get(key) != value
                                  for key, value in expected_v6.items()):
        failures.append("v6_clean_decision_drift")

    mutation_failures = []
    for row in rows:
        if type(row) is not dict:
            continue
        mutant = {**row, "planner_window": dict(row.get("planner_window") or {})}
        duration = mutant["planner_window"].get("duration_ns")
        if type(duration) is not int:
            mutation_failures.append("mutation_control_input_not_integer")
            continue
        mutant["planner_window"]["duration_ns"] = duration + 1
        errors = row_errors(mutant)
        if errors != [f"pair{row.get('pair_index')}:{row.get('arm')}:planner_window_duration_mismatch"]:
            mutation_failures.append(
                f"pair{row.get('pair_index')}:{row.get('arm')}:mutation_not_isolated"
            )
    if len(mutation_failures) != 0 or len(rows) != 6:
        failures.extend(mutation_failures or ["mutation_control_count"])

    long_probe = {
        "pair_index": 99,
        "arm": "self_consistent_3_6s_probe",
        "planner_window": {
            "start_ns": 1_000_000_000,
            "end_ns": 4_600_000_000,
            "duration_ns": 3_600_000_000,
            "end_boundary_phase": PHASE,
        },
    }
    long_probe_errors = row_errors(long_probe)
    return {
        "schema": "map01-recovery-v6-window-integrity-audit-v1",
        "decision": "PASS_WINDOW_ARITHMETIC_AUDIT_SCOPED" if not failures else "FAIL",
        "valid_fixture": not failures,
        "failures": failures,
        "arm_count": len(rows),
        "single_arm_duration_mutations_rejected": 6 - len(mutation_failures),
        "mutation_failures": mutation_failures,
        "self_consistent_3_6s_probe": {
            "arithmetic_errors": long_probe_errors,
            "passes_narrow_arithmetic_predicate": not long_probe_errors,
            "disposition": "OUTSIDE_CLAIM_NO_UPPER_DURATION_BOUND",
        },
        "claim_scope": (
            "synthetic self-consistency between retained duration_ns and "
            "end_ns-start_ns plus frozen phase-string checking only"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = inspect(payload)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.out.write_text(text, encoding="utf-8")
    print(json.dumps({"audit": result["decision"],
                      "rejected_mutations": result["single_arm_duration_mutations_rejected"],
                      "failures": result["failures"]}, sort_keys=True))
    return 0 if result["valid_fixture"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
