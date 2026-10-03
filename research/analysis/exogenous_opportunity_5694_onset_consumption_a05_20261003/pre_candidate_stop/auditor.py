"""Independent raw-only reconstruction; deliberately does not import candidate.py."""
import argparse
import copy
import json
from pathlib import Path


def expected_for(case, oracle):
    if case["cue_window"] is None:
        derived = {"boundary":"NOT_APPLICABLE","reason":"no_exogenous_opportunity","capture":None,"receipt":None}
    elif not case["clock_synchronized"]:
        derived = {"boundary":"UNKNOWN","reason":"clock_unsynced","capture":None,"receipt":None}
    else:
        cue = case["cue_window"]
        if case["observation_horizon_ms"] < cue["expiry_ms"] and case["effect_receipt_id"] is None and case["safe_stop_ms"] is None:
            derived = {"boundary":"UNKNOWN","reason":"right_censored","capture":None,"receipt":None}
        else:
            eligible = [t for t in case["capture_times_ms"] if cue["onset_ms"] <= t <= cue["expiry_ms"]]
            first_capture = min(eligible) if eligible else None
            if first_capture is None:
                derived = {"boundary":"not_acquired","reason":"no_capture_inside_cue_window","capture":None,"receipt":None}
            elif case["delivery_ms"] is None:
                derived = {"boundary":"acquired_not_delivered","reason":"no_delivery_before_expiry","capture":first_capture,"receipt":None}
            elif case["delivery_ms"] > cue["expiry_ms"]:
                derived = {"boundary":"acquired_not_delivered","reason":"delivery_after_expiry","capture":first_capture,"receipt":None}
            elif case["decision_ms"] is None or case["decision_ms"] > cue["expiry_ms"]:
                derived = {"boundary":"delivered_no_decision","reason":"no_decision_before_expiry","capture":first_capture,"receipt":None}
            elif case["safe_stop_ms"] is not None:
                derived = {"boundary":"decision_no_effect","reason":"safe_stop","capture":first_capture,"receipt":None}
            elif case["effect_receipt_id"] is None:
                derived = {"boundary":"decision_no_effect","reason":"no_verified_effect","capture":first_capture,"receipt":None}
            else:
                derived = {"boundary":"eligible_effect","reason":"verified_effect","capture":first_capture,"receipt":case["effect_receipt_id"]}
    ref = oracle["expected"][case["case_id"]]
    if derived["boundary"] != ref["boundary"] or derived["reason"] != ref["reason"] or derived["capture"] != ref["first_acquisition_capture_ms"] or derived["receipt"] != ref["effect_receipt_id"]:
        return {"boundary":"FAIL_AUDIT","reason":"fixture_oracle_inconsistency","capture":None,"receipt":None}
    return derived


def audit_once(fixture, oracle, raw):
    errors = []
    cases = {c["case_id"]: c for c in fixture["cases"]}
    rows = raw.get("rows", [])
    ids = [r.get("case_id") for r in rows]
    if raw.get("schema") != "exogenous-opportunity-onset-consumption-raw-v1" or raw.get("fixture_id") != fixture["fixture_id"]:
        errors.append("raw_identity_mismatch")
    if len(ids) != len(set(ids)) or set(ids) != set(cases):
        errors.append("row_identity_or_count_mismatch")
    by_id = {r.get("case_id"): r for r in rows}
    left, right = (cases[x] for x in fixture["phase_pair"])
    def normalized(case):
        value = copy.deepcopy(case)
        value.pop("case_id", None)
        value["cue_window"].pop("onset_ms", None)
        return value
    if normalized(left) != normalized(right):
        errors.append("phase_pair_differs_beyond_onset")
    for case_id, case in cases.items():
        row = by_id.get(case_id)
        if row is None:
            continue
        want = expected_for(case, oracle)
        if row.get("boundary") != want["boundary"] or row.get("reason") != want["reason"]:
            errors.append(f"classification_mismatch:{case_id}")
        if row.get("first_acquisition_capture_ms") != want["capture"]:
            errors.append(f"acquisition_time_mismatch:{case_id}")
        if row.get("effect_receipt_id") != want["receipt"]:
            errors.append(f"receipt_mismatch:{case_id}")
        if row.get("capture_times_ms") != case["capture_times_ms"] or row.get("observation_horizon_ms") != case["observation_horizon_ms"]:
            errors.append(f"capture_schedule_or_horizon_mismatch:{case_id}")
    return {"rows_replayed":len(rows),"errors":errors,"result":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}


def audit(fixture, oracle, raw):
    base = audit_once(fixture, oracle, raw)
    mutants = []
    missing = copy.deepcopy(raw); missing["rows"].pop()
    mutants.append(("missing_row", missing))
    duplicate = copy.deepcopy(raw); duplicate["rows"].append(copy.deepcopy(duplicate["rows"][0]))
    mutants.append(("duplicate_row", duplicate))
    wrong_capture = copy.deepcopy(raw)
    next(r for r in wrong_capture["rows"] if r["case_id"] == "c02")["first_acquisition_capture_ms"] = 10
    mutants.append(("forged_phase_capture", wrong_capture))
    schedule = copy.deepcopy(raw)
    next(r for r in schedule["rows"] if r["case_id"] == "c02")["capture_times_ms"] = [10, 51]
    mutants.append(("changed_schedule", schedule))
    forged = copy.deepcopy(raw)
    row = next(r for r in forged["rows"] if r["case_id"] == "c05")
    row["boundary"] = "eligible_effect"; row["reason"] = "verified_effect"; row["effect_receipt_id"] = "forged"
    mutants.append(("forged_effect_receipt", forged))
    controls = {}
    for name, mutant in mutants:
        controls[name] = bool(audit_once(fixture, oracle, mutant)["errors"])
    base["corruption_controls"] = controls
    base["corruptions_rejected"] = sum(controls.values())
    base["result"] = "PASS_METHOD_SCOPED" if base["result"] == "PASS_METHOD_SCOPED" and all(controls.values()) else "FAIL_AUDIT"
    return base


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
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"rows_replayed={result['rows_replayed']}")
    print(f"errors={len(result['errors'])}")
    print(f"corruptions_rejected={result['corruptions_rejected']}/5")
    print(result["result"])


if __name__ == "__main__":
    main()