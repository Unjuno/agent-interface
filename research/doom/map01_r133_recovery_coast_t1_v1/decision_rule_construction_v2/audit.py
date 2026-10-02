"""Independent raw-only finite oracle for construction v2; imports no candidate code."""
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
    "identity_hash_malformed": ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_format:model_contract_sha256"),
    "source_identity_mismatch": ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_mismatch:source_bundle_sha256"),
    "unverified_release": ("FAIL_SAFETY", "STOP_SAFETY", "terminal_release"),
    "stale_action": ("FAIL_SAFETY", "STOP_SAFETY", "stale_action"),
    "fixture_mismatch": ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_mismatch:fixture_sha256"),
    "pair_start_mismatch": ("STOP_INTEGRITY", "STOP_INTEGRITY", "pair_start_mismatch"),
    "duplicate_session": ("STOP_INTEGRITY", "STOP_INTEGRITY", "session_id_duplicate"),
    "wrong_counterbalance": ("STOP_INTEGRITY", "STOP_INTEGRITY", "counterbalance_order"),
    "incomplete_audit": ("STOP_INTEGRITY", "STOP_INTEGRITY", "incomplete_or_audit_errors"),
    "bad_exposure_interval": ("STOP_INTEGRITY", "STOP_INTEGRITY", "exposure_bounds"),
}


def oracle(p, e):
    pw, pl = sum(x == 1 for x in p), sum(x == -1 for x in p)
    ew, el = sum(x == -1 for x in e), sum(x == 1 for x in e)
    if pw >= 2 and pl == 0 and ew >= 2 and el == 0:
        return "PASS_DIRECTIONAL_FIXTURE_SCOPED"
    if pl >= 2 and pw == 0 and el >= 2 and ew == 0:
        return "FAIL_DIRECTIONAL_FIXTURE_SCOPED"
    return "UNCERTAIN"


def audit_cases(cases):
    errors, expected, actual = [], set(), set()
    for p in itertools.product((-1, 0, 1), repeat=3):
        for e in itertools.product((-1, 0, 1), repeat=3):
            expected.add((p, e))
    if not isinstance(cases, list):
        return ["cases_not_list"]
    for row in cases:
        if not isinstance(row, dict):
            errors.append("case_not_object")
            continue
        try:
            key = (tuple(row["progress_signs"]), tuple(row["exposure_signs"]))
        except (KeyError, TypeError):
            errors.append("case_key_missing")
            continue
        if key in actual:
            errors.append("case_duplicate")
        actual.add(key)
        if key not in expected:
            errors.append("case_unexpected")
            continue
        if row.get("result") != oracle(*key) or row.get("integrated_status") != oracle(*key):
            errors.append("oracle_mismatch")
        if row.get("instrumentation_status") != "PASS_INSTRUMENTATION_AND_RELEASE":
            errors.append("instrumentation_gate_mismatch")
    if actual != expected:
        errors.append("case_inventory")
    return sorted(set(errors))


def controls_bad(controls):
    if not isinstance(controls, dict) or set(controls) != set(EXPECTED_CONTROLS):
        return True
    for name, wanted in EXPECTED_CONTROLS.items():
        row = controls.get(name)
        if not isinstance(row, dict):
            return True
        observed = (row.get("instrumentation_status"), row.get("comparative_status"), row.get("reason"))
        if observed != wanted or tuple(row.get("expected", ())) != wanted:
            return True
    return False


def forge_tie_pass(value):
    for row in value["cases"]:
        if tuple(row["progress_signs"]) == (0, 0, 0) and tuple(row["exposure_signs"]) == (0, 0, 0):
            row["result"] = row["integrated_status"] = "PASS_DIRECTIONAL_FIXTURE_SCOPED"
            return


def main():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    source_errors = []
    for name, expected in freeze["pinned_sha256"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            source_errors.append("source_hash:" + name)
    raw_bytes, run_bytes = (OUT / "RAW.json").read_bytes(), (OUT / "RUN.json").read_bytes()
    raw, run = json.loads(raw_bytes), json.loads(run_bytes)
    if run.get("raw_sha256") != hashlib.sha256(raw_bytes).hexdigest():
        source_errors.append("raw_receipt_hash")
    if raw.get("freeze_sha256") != hashlib.sha256(FREEZE.read_bytes()).hexdigest():
        source_errors.append("freeze_hash")
    if raw.get("candidate_sha256") != hashlib.sha256((HERE / "candidate.py").read_bytes()).hexdigest():
        source_errors.append("candidate_hash")
    cases = raw.get("cases")
    case_errors = audit_cases(cases)
    if raw.get("case_count") != 729 or not isinstance(cases, list) or len(cases) != 729:
        case_errors.append("case_count")
    controls = raw.get("control_cases")
    control_errors = ["control_mismatch"] if controls_bad(controls) else []
    mutation_results = {}
    mutations = [
        ("omitted_case", lambda x: x["cases"].pop()),
        ("forged_tie_pass", forge_tie_pass),
        ("duplicate_case", lambda x: x["cases"].__setitem__(-1, copy.deepcopy(x["cases"][0]))),
        ("mutated_control", lambda x: x["control_cases"]["identity_hash_malformed"].update(reason="other")),
    ]
    for name, mutate in mutations:
        altered = copy.deepcopy(raw)
        mutate(altered)
        rejected = bool(audit_cases(altered.get("cases"))) or controls_bad(altered.get("control_cases"))
        mutation_results[name] = {"rejected": rejected}
        if not rejected:
            control_errors.append("mutation_accepted:" + name)
    errors = source_errors + case_errors + control_errors
    result = {"schema": "t1-paired-rule-construction-audit-v2",
              "status": "PASS_T1_IDENTITY_PRECEDENCE_CONSTRUCTION" if not errors else "FAIL_AUDIT",
              "source_errors": source_errors, "case_errors": case_errors,
              "control_errors": control_errors, "oracle_cases": 729,
              "candidate_cases": len(cases) if isinstance(cases, list) else None,
              "oracle_mismatches": case_errors.count("oracle_mismatch"),
              "control_results": controls, "raw_mutations": mutation_results,
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "scope": "synthetic adjudicator construction only; no live T1 evidence or authorization"}
    (OUT / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
