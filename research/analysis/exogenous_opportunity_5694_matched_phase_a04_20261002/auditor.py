"""Independent raw-only reconstruction; deliberately does not import candidate.py."""
import argparse
import copy
import json
from pathlib import Path


def expected_for(case, oracle):
    if case["opportunity"] is None:
        return {"boundary":"NOT_APPLICABLE", "reason":"no_exogenous_opportunity", "receipt":None}
    key = case["case_id"]
    if not case["clock_synchronized"]:
        derived = {"boundary":"UNKNOWN", "reason":"clock_unsynced", "receipt":None}
    else:
        opp = case["opportunity"]
        expiry = opp["expiry_ms"]
        if case["observation_horizon_ms"] < expiry and case["effect_receipt_id"] is None and case["safe_stop_ms"] is None:
            derived = {"boundary":"UNKNOWN", "reason":"right_censored", "receipt":None}
        else:
            captured = any(cap["at_ms"] <= expiry and case["opportunity_id"] in cap["opportunity_ids"] for cap in case["captures"])
            if not captured:
                derived = {"boundary":"not_acquired", "reason":"no_capture_before_expiry", "receipt":None}
            elif case["delivery_ms"] is None or case["delivery_ms"] > expiry:
                derived = {"boundary":"acquired_not_delivered", "reason":"delivery_after_expiry", "receipt":None}
            elif case["decision_ms"] is None or case["decision_ms"] > expiry:
                derived = {"boundary":"delivered_no_decision", "reason":"no_decision_before_expiry", "receipt":None}
            elif case["safe_stop_ms"] is not None:
                derived = {"boundary":"decision_no_effect", "reason":"safe_stop", "receipt":None}
            elif case["effect_receipt_id"] is None:
                derived = {"boundary":"decision_no_effect", "reason":"no_verified_effect", "receipt":None}
            else:
                derived = {"boundary":"eligible_effect", "reason":"verified_effect", "receipt":case["effect_receipt_id"]}
    if derived["boundary"] != oracle[key]["boundary"] or derived["reason"] != oracle[key]["reason"] or derived["receipt"] != oracle[key]["receipt"]:
        return {"boundary":"FAIL_AUDIT", "reason":"fixture_oracle_inconsistency", "receipt":None}
    return derived


def audit_once(fixture, oracle, raw):
    errors = []
    cases = {c["case_id"]: c for c in fixture["cases"]}
    expected_ids = set(cases)
    rows = raw.get("rows", [])
    ids = [r.get("case_id") for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != expected_ids:
        errors.append("row_identity_or_count_mismatch")
    by_id = {r.get("case_id"): r for r in rows}
    pair = fixture["phase_pair"]
    left, right = (cases[x] for x in pair)
    if left["capture_schedule_ms"] != right["capture_schedule_ms"]:
        errors.append("phase_capture_schedule_not_matched")
    if left["observation_horizon_ms"] != right["observation_horizon_ms"]:
        errors.append("phase_horizon_not_matched")
    if left["opportunity"]["expiry_ms"] != right["opportunity"]["expiry_ms"]:
        errors.append("phase_expiry_not_matched")
    for case_id, case in cases.items():
        row = by_id.get(case_id)
        if row is None:
            continue
        want = expected_for(case, oracle["expected"])
        if row.get("boundary") != want["boundary"] or row.get("reason") != want["reason"]:
            errors.append(f"classification_mismatch:{case_id}")
        if row.get("effect_receipt_id") != want["receipt"]:
            errors.append(f"receipt_mismatch:{case_id}")
        if row.get("capture_schedule_ms") != case["capture_schedule_ms"] or row.get("observation_horizon_ms") != case["observation_horizon_ms"]:
            errors.append(f"schedule_or_horizon_mismatch:{case_id}")
    return {"rows_replayed":len(rows), "errors":errors, "result":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}


def audit(fixture, oracle, raw):
    base = audit_once(fixture, oracle, raw)
    mutants = []
    missing = copy.deepcopy(raw); missing["rows"].pop()
    mutants.append(("missing_row", missing))
    duplicate = copy.deepcopy(raw); duplicate["rows"].append(copy.deepcopy(duplicate["rows"][0]))
    mutants.append(("duplicate_row", duplicate))
    wrong = copy.deepcopy(raw)
    next(r for r in wrong["rows"] if r["case_id"] == "c02")["boundary"] = "eligible_effect"
    mutants.append(("wrong_phase_classification", wrong))
    schedule = copy.deepcopy(raw)
    next(r for r in schedule["rows"] if r["case_id"] == "c02")["capture_schedule_ms"] = [10, 55]
    mutants.append(("changed_capture_schedule", schedule))
    forged = copy.deepcopy(raw)
    forged_row = next(r for r in forged["rows"] if r["case_id"] == "c05")
    forged_row.update(boundary="eligible_effect", reason="verified_effect", effect_receipt_id="forged")
    mutants.append(("forged_effect_receipt", forged))
    controls = {name: bool(audit_once(fixture, oracle, mutated)["errors"]) for name, mutated in mutants}
    errors = list(base["errors"])
    errors.extend("corruption_accepted:" + name for name, rejected in controls.items() if not rejected)
    return {
        "rows_replayed": base["rows_replayed"],
        "errors": errors,
        "corruptions_rejected": sum(controls.values()),
        "corruption_controls": controls,
        "result": "PASS_METHOD_SCOPED" if not errors and all(controls.values()) else "FAIL_AUDIT",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    oracle = json.loads(Path(args.oracle).read_text(encoding="utf-8"))
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    result = audit(fixture, oracle, raw)
    Path(args.out).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"rows_replayed={result['rows_replayed']}")
    print(f"errors={result['errors']}")
    print("AUDIT_" + result["result"])
    raise SystemExit(0 if result["result"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
