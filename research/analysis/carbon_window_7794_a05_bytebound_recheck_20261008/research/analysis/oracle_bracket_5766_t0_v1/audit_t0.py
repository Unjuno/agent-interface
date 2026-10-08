"""Independent replay of frozen references and bracket dispositions."""
import json
from pathlib import Path
import hashlib


def reference_score(case):
    r = case["record"]
    if r["status"] == "PARTIAL":
        return "UNKNOWN"
    return "PASS" if (r["status"] == "COMPLETE" and r["target"] == "expected"
                      and r["durable"] is True and r["collateral"] is False) else "FAIL"


def audit(spec, raw):
    errors = []
    if spec["reference_timestamp"] != "before-candidate":
        errors.append("reference_not_frozen_before_candidate")
    scorer_path = Path(__file__).with_name("scorer_v1.py")
    recomputed_sha = hashlib.sha256(scorer_path.read_bytes()).hexdigest().upper()
    if spec["scorer_sha256"] != recomputed_sha:
        errors.append("scorer_identity_changed")
    deck = spec["check_deck"]
    expected = [reference_score(item) for item in deck]
    for item, label in zip(deck, expected):
        if item["expected"] != label:
            errors.append("reference_label_mismatch:" + item["id"])
    raw_scenarios = raw.get("scenarios", {})
    if set(raw_scenarios) != set(spec["scenarios"]):
        errors.append("scenario_coverage_mismatch")
    blocked = 0
    equivalent_rejected = 0
    for name, scenario in spec["scenarios"].items():
        result = raw_scenarios.get(name, {})
        pre = list(expected)
        post = list(expected)
        if scenario["drift_case"]:
            idx = next(i for i, item in enumerate(deck) if item["id"] == scenario["drift_case"])
            post[idx] = reference_score({"record": scenario["post_record"]})
        if result.get("precheck") != pre:
            errors.append("precheck_mismatch:" + name)
        if result.get("postcheck") != post:
            errors.append("postcheck_mismatch:" + name)
        rows = result.get("candidate_rows", [])
        if len(rows) != len(spec["candidate_rows"]):
            errors.append("candidate_row_count_mismatch:" + name)
        for idx, row in enumerate(rows):
            if idx >= len(spec["candidate_rows"]):
                errors.append("extra_candidate_row:" + name)
                break
            frozen = spec["candidate_rows"][idx]
            scored = reference_score({"record": frozen["record"]})
            expected_truth = scenario.get("candidate_truth_overrides", {}).get(frozen["id"], frozen["reference"])
            if row != {"id": frozen["id"], "scored": scored, "reference": expected_truth}:
                errors.append("candidate_row_mismatch:" + name)
        wanted = ("UNKNOWN_COVERAGE" if scenario["outside_deck"] else
                  "HOLD_ORACLE_DRIFT" if post != pre else "PASS")
        if result.get("promotion") != wanted:
            errors.append("promotion_mismatch:" + name)
        false_promotions = [row for row in result.get("candidate_rows", [])
                            if row.get("scored") == "PASS" and row.get("reference") == "FAIL"]
        if false_promotions and result.get("promotion") == "HOLD_ORACLE_DRIFT":
            blocked += len(false_promotions)
        elif false_promotions:
            errors.append("false_candidate_promotion_not_blocked:" + name)
        if scenario["scorer_version"] != "s1" and wanted == "PASS" and result.get("promotion") != "PASS":
            equivalent_rejected += 1
    if raw.get("reference_timestamp") != "before-candidate":
        errors.append("raw_reference_backfilled")
    return {"schema": "oracle-bracket-5766-audit-v1",
            "status": "PASS_METHOD_SCOPED" if not errors and blocked == 1 and equivalent_rejected == 0 else "FAIL",
            "deck_cases": len(deck), "scenarios": len(spec["scenarios"]),
            "false_promotions_blocked": blocked, "equivalent_version_rejected": equivalent_rejected,
            "out_of_deck_disposition": raw_scenarios.get("out_of_deck_drift", {}).get("promotion"),
            "errors": errors}


if __name__ == "__main__":
    with open("spec.json", encoding="utf-8") as f:
        spec = json.load(f)
    with open("raw.json", encoding="utf-8") as f:
        raw = json.load(f)
    result = audit(spec, raw)
    with open("audit.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
