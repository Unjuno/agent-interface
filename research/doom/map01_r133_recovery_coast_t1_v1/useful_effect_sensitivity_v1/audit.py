#!/usr/bin/env python3
"""Independent raw-only oracle for the finite gate-sensitivity sweep."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / "results" / "sensitivity-01"
FREEZE = HERE / "FREEZE.json"
FIXTURE = HERE / "FIXTURE.json"
SOURCE = ROOT / "research/doom/map01_r133_recovery_coast_t1_v1/decision_rule_construction_v2/adjudicator.py"
EXPECTED_PATTERNS = {
    "neither": (False, False), "coast_only": (False, True),
    "recovery_only": (True, False), "both": (True, True),
}
EXPECTED_CONTROLS = {
    "no_threat_positive_event": "HOLD_NOT_EVALUATED",
    "no_event_with_threat": "HOLD_NOT_EVALUATED",
    "positive_control": "PASS_DIRECTIONAL_FIXTURE_SCOPED",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def oracle(progress, exposure, threat_present, useful_present):
    if not threat_present or not useful_present:
        return "HOLD_NOT_EVALUATED"
    progress_wins = sum(value == 1 for value in progress)
    progress_losses = sum(value == -1 for value in progress)
    exposure_wins = sum(value == -1 for value in exposure)
    exposure_losses = sum(value == 1 for value in exposure)
    if progress_wins >= 2 and progress_losses == 0 and exposure_wins >= 2 and exposure_losses == 0:
        return "PASS_DIRECTIONAL_FIXTURE_SCOPED"
    if progress_losses >= 2 and progress_wins == 0 and exposure_losses >= 2 and exposure_wins == 0:
        return "FAIL_DIRECTIONAL_FIXTURE_SCOPED"
    return "UNCERTAIN"


def audit_rows(rows):
    errors = []
    expected = set()
    for progress in itertools.product((-1, 0, 1), repeat=3):
        for exposure in itertools.product((-1, 0, 1), repeat=3):
            for pattern in EXPECTED_PATTERNS:
                expected.add((progress, exposure, pattern))
    observed = set()
    if not isinstance(rows, list):
        return ["rows_not_list"]
    for row in rows:
        if not isinstance(row, dict):
            errors.append("row_not_object")
            continue
        try:
            progress = tuple(row["progress_signs"])
            exposure = tuple(row["exposure_signs"])
            pattern = row["event_pattern"]
            key = (progress, exposure, pattern)
        except (KeyError, TypeError):
            errors.append("row_key_missing")
            continue
        if key in observed:
            errors.append("duplicate_row")
        observed.add(key)
        if key not in expected:
            errors.append("unexpected_row")
            continue
        recovery, coast = EXPECTED_PATTERNS[pattern]
        if (row.get("recovery_positive"), row.get("coast_positive")) != (recovery, coast):
            errors.append("arm_membership_mismatch")
        if row.get("legacy_useful_present") is not (recovery or coast):
            errors.append("legacy_gate_input_mismatch")
        if row.get("recovery_useful_present") is not recovery:
            errors.append("recovery_gate_input_mismatch")
        if row.get("legacy_status") != oracle(progress, exposure, True, recovery or coast):
            errors.append("legacy_oracle_mismatch")
        if row.get("recovery_gated_status") != oracle(progress, exposure, True, recovery):
            errors.append("recovery_oracle_mismatch")
    if observed != expected:
        errors.append("case_inventory_mismatch")
    return sorted(set(errors))


def main() -> int:
    freeze_bytes = FREEZE.read_bytes()
    freeze = json.loads(freeze_bytes)
    raw_bytes = (OUT / "RAW.json").read_bytes()
    run = json.loads((OUT / "RUN.json").read_text(encoding="utf-8"))
    raw = json.loads(raw_bytes)
    source_paths = {"PLAN.md": HERE / "PLAN.md", "FIXTURE.json": FIXTURE,
                    "candidate.py": HERE / "candidate.py", "audit.py": Path(__file__),
                    "adjudicator.py": SOURCE}
    source_errors = ["source_hash:" + name for name, path in source_paths.items()
                     if sha_bytes(path.read_bytes()) != freeze["pinned_sha256"][name]]
    if run.get("raw_sha256") != sha_bytes(raw_bytes):
        source_errors.append("run_raw_hash")
    if raw.get("freeze_sha256") != sha_bytes(freeze_bytes):
        source_errors.append("raw_freeze_hash")
    if raw.get("fixture_sha256") != sha_bytes(FIXTURE.read_bytes()):
        source_errors.append("raw_fixture_hash")
    if raw.get("adjudicator_sha256") != sha_bytes(SOURCE.read_bytes()):
        source_errors.append("raw_adjudicator_hash")
    errors = source_errors + audit_rows(raw.get("rows"))
    if raw.get("schema") != "r133-useful-effect-sensitivity-raw-v1" or raw.get("row_count") != 2916:
        errors.append("raw_schema_or_count")
    controls = raw.get("controls")
    if controls != EXPECTED_CONTROLS:
        errors.append("control_mismatch")
    mutation_results = {}
    mutations = {
        "drop_case": lambda value: value["rows"].pop(),
        "forge_legacy_pass": lambda value: value["rows"][0].update(legacy_status="PASS_DIRECTIONAL_FIXTURE_SCOPED"),
        "forge_arm_membership": lambda value: value["rows"][0].update(recovery_positive=True),
    }
    for name, mutate in mutations.items():
        altered = copy.deepcopy(raw)
        mutate(altered)
        rejected = bool(audit_rows(altered.get("rows")))
        mutation_results[name] = {"rejected": rejected}
        if not rejected:
            errors.append("mutation_accepted:" + name)
    by_pattern = {}
    transitions = {}
    for row in raw.get("rows", []):
        pattern = row["event_pattern"]
        by_pattern.setdefault(pattern, {})
        key = row["legacy_status"]
        by_pattern[pattern][key] = by_pattern[pattern].get(key, 0) + 1
        pair = row["legacy_status"] + " -> " + row["recovery_gated_status"]
        transitions[pair] = transitions.get(pair, 0) + 1
    disposition = "PASS_SENSITIVITY_SCOPED" if not errors else "FAIL_AUDIT"
    result = {"schema": "r133-useful-effect-sensitivity-audit-v1", "status": disposition,
              "errors": sorted(set(errors)), "case_count": len(raw.get("rows", [])),
              "gate_pattern_legacy_counts": by_pattern, "gate_transitions": transitions,
              "mutations": mutation_results,
              "scope": "finite abstract comparator-input sensitivity only; not live or empirical evidence"}
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    (OUT / "AUDIT.json").write_text(encoded, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if disposition == "PASS_SENSITIVITY_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
