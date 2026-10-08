import argparse
import hashlib
import json
from pathlib import Path


ROW_KEYS = {"case_id", "predicate_id", "scorer_id", "evidence_sha256", "computed_true",
            "commitment_ms", "outcome_ms", "capture_age_ms", "coverage_scope",
            "origin_attested", "task_effect_claim", "whole_task_success"}


def predicate_result(case, fixture):
    evidence = case["evidence"]
    if case["predicate_id"] == "effect_exact_v1":
        p = fixture["predicate"]
        return any(event.get("target") == p["target"] and event.get("effect") == p["effect"]
                   and event.get("receipt") == p["receipt"] for event in evidence.get("events", []))
    if case["predicate_id"] == "visibility_only_v1":
        return evidence.get("visible_label") == "submit"
    raise ValueError("unknown synthetic predicate")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture_bytes = Path(args.fixture).read_bytes()
    fixture = json.loads(fixture_bytes)
    rows = []
    for case in fixture["cases"]:
        evidence_bytes = json.dumps(case["evidence"], sort_keys=True, separators=(",", ":")).encode("utf-8")
        rows.append({
            "case_id": case["case_id"], "predicate_id": case["predicate_id"],
            "scorer_id": case["scorer_id"], "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "computed_true": predicate_result(case, fixture), "commitment_ms": case["commitment_ms"],
            "outcome_ms": case["outcome_ms"], "capture_age_ms": case["capture_age_ms"],
            "coverage_scope": case["coverage_scope"], "origin_attested": case["origin_attested"],
            "task_effect_claim": "NOT_ESTABLISHED_BY_T0", "whole_task_success": False,
        })
    raw = {"schema": "private-witness-boundary-candidate-v1",
           "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
           "case_order": [case["case_id"] for case in fixture["cases"]], "rows": rows}
    Path(args.output).write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
