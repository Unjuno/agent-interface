"""Independent raw-only oracle for the T1 paired adjudication rule."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "construction-01"
FREEZE = HERE / "FREEZE.json"


EXPECTED_CONTROLS = {
    "no_threat": ("PASS_INSTRUMENTATION_AND_RELEASE", "HOLD_NOT_EVALUATED", None),
    "no_useful_event": ("PASS_INSTRUMENTATION_AND_RELEASE", "HOLD_NOT_EVALUATED", None),
    "unverified_release": ("FAIL_SAFETY", "STOP_SAFETY", "terminal_release"),
    "stale_action": ("FAIL_SAFETY", "STOP_SAFETY", "stale_action"),
    "fixture_mismatch": ("STOP_INTEGRITY", "STOP_INTEGRITY", "fixture_mismatch"),
    "identity_hash_malformed": ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_format:model_contract_sha256"),
    "pair_start_mismatch": ("STOP_INTEGRITY", "STOP_INTEGRITY", "pair_start_mismatch"),
    "duplicate_session": ("STOP_INTEGRITY", "STOP_INTEGRITY", "session_id_duplicate"),
    "wrong_counterbalance": ("STOP_INTEGRITY", "STOP_INTEGRITY", "counterbalance_order"),
    "incomplete_audit": ("STOP_INTEGRITY", "STOP_INTEGRITY", "incomplete_or_audit_errors"),
    "bad_exposure_interval": ("STOP_INTEGRITY", "STOP_INTEGRITY", "exposure_bounds"),
    "source_drift_identity": ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_mismatch:source_bundle_sha256"),
}


def oracle(progress: tuple[int, ...], exposure: tuple[int, ...]) -> str:
    progress_wins = sum(sign == 1 for sign in progress)
    progress_losses = sum(sign == -1 for sign in progress)
    exposure_wins = sum(sign == -1 for sign in exposure)
    exposure_losses = sum(sign == 1 for sign in exposure)
    recovery_only = (progress_wins >= 2 and progress_losses == 0
                     and exposure_wins >= 2 and exposure_losses == 0)
    coast_only = (progress_losses >= 2 and progress_wins == 0
                  and exposure_losses >= 2 and exposure_wins == 0)
    if recovery_only:
        return "PASS_DIRECTIONAL_FIXTURE_SCOPED"
    if coast_only:
        return "FAIL_DIRECTIONAL_FIXTURE_SCOPED"
    return "UNCERTAIN"


def audit_cases(cases) -> list[str]:
    errors = []
    expected_keys = set()
    actual_keys = set()
    if not isinstance(cases, list):
        return ["cases_not_list"]
    for progress in itertools.product((-1, 0, 1), repeat=3):
        for exposure in itertools.product((-1, 0, 1), repeat=3):
            expected_keys.add((progress, exposure))
    for row in cases:
        if not isinstance(row, dict):
            errors.append("case_not_object")
            continue
        try:
            key = (tuple(row["progress_signs"]), tuple(row["exposure_signs"]))
        except (KeyError, TypeError):
            errors.append("case_key_missing")
            continue
        if key in actual_keys:
            errors.append("case_duplicate")
        actual_keys.add(key)
        if key not in expected_keys:
            errors.append("case_unexpected")
            continue
        expected = oracle(*key)
        if row.get("result") != expected or row.get("integrated_status") != expected:
            errors.append("oracle_mismatch")
        if row.get("instrumentation_status") != "PASS_INSTRUMENTATION_AND_RELEASE":
            errors.append("instrumentation_gate_mismatch")
    if actual_keys != expected_keys:
        errors.append("case_inventory")
    return sorted(set(errors))


def main() -> int:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    source_errors = []
    for name, expected in freeze["pinned_sha256"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            source_errors.append("source_hash:" + name)
    run_path, raw_path = OUT / "RUN.json", OUT / "RAW.json"
    run_bytes, raw_bytes = run_path.read_bytes(), raw_path.read_bytes()
    run, raw = json.loads(run_bytes), json.loads(raw_bytes)
    if hashlib.sha256(raw_bytes).hexdigest() != run.get("raw_sha256"):
        source_errors.append("raw_receipt_hash")
    if raw.get("freeze_sha256") != hashlib.sha256(FREEZE.read_bytes()).hexdigest():
        source_errors.append("freeze_hash")
    if raw.get("candidate_sha256") != hashlib.sha256((HERE / "candidate.py").read_bytes()).hexdigest():
        source_errors.append("candidate_hash")
    cases = raw.get("cases")
    case_errors = audit_cases(cases)
    if raw.get("case_count") != 729 or len(cases) != 729:
        case_errors.append("case_count")

    raw_controls = raw.get("control_cases")
    control_errors = []
    if not isinstance(raw_controls, dict) or set(raw_controls) != set(EXPECTED_CONTROLS):
        control_errors.append("control_inventory")
        raw_controls = raw_controls if isinstance(raw_controls, dict) else {}
    for name, expected in EXPECTED_CONTROLS.items():
        row = raw_controls.get(name)
        if not isinstance(row, dict):
            control_errors.append("control_missing:" + name)
            continue
        observed = (row.get("instrumentation_status"), row.get("comparative_status"), row.get("reason"))
        if observed != expected or tuple(row.get("expected", ())) != expected:
            control_errors.append("control_result:" + name)

    mutation_results = {}
    mutation_values = [
        ("omitted_case", lambda value: value["cases"].pop()),
        ("forged_pass", lambda value: _forge_case(value)),
        ("duplicate_case", lambda value: value["cases"].__setitem__(-1, copy.deepcopy(value["cases"][0]))),
        ("control_status", lambda value: value["control_cases"]["unverified_release"].update(
            instrumentation_status="PASS_INSTRUMENTATION_AND_RELEASE", comparative_status="PASS_DIRECTIONAL_FIXTURE_SCOPED")),
    ]
    for name, mutate in mutation_values:
        changed = copy.deepcopy(raw)
        mutate(changed)
        rejected = bool(audit_cases(changed.get("cases"))) or _control_mutated(changed.get("control_cases"))
        mutation_results[name] = {"rejected": rejected}
        if not rejected:
            control_errors.append("mutation_accepted:" + name)

    errors = source_errors + case_errors + control_errors
    result = {
        "schema": "t1-paired-rule-construction-audit-v1",
        "status": "PASS_T1_DIRECTIONAL_ADJUDICATOR_CONSTRUCTION" if not errors else "FAIL_AUDIT",
        "source_errors": source_errors,
        "case_errors": case_errors,
        "control_errors": control_errors,
        "oracle_cases": 729,
        "candidate_cases": len(cases) if isinstance(cases, list) else None,
        "oracle_mismatches": sum(1 for error in case_errors if error == "oracle_mismatch"),
        "control_results": raw_controls,
        "raw_mutations": mutation_results,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "scope": "synthetic adjudicator construction only; not live preregistration acceptance or experiment evidence",
    }
    (OUT / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


def _forge_case(value: dict) -> None:
    for row in value["cases"]:
        if tuple(row["progress_signs"]) == (0, 0, 0) and tuple(row["exposure_signs"]) == (0, 0, 0):
            row["result"] = "PASS_DIRECTIONAL_FIXTURE_SCOPED"
            row["integrated_status"] = "PASS_DIRECTIONAL_FIXTURE_SCOPED"
            return


def _control_mutated(controls) -> bool:
    if not isinstance(controls, dict):
        return True
    for name, expected in EXPECTED_CONTROLS.items():
        row = controls.get(name)
        if not isinstance(row, dict):
            return True
        observed = (row.get("instrumentation_status"), row.get("comparative_status"), row.get("reason"))
        if observed != expected:
            return True
    return set(controls) != set(EXPECTED_CONTROLS)


if __name__ == "__main__":
    raise SystemExit(main())
