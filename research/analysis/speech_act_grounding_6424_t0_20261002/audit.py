"""Raw-only audit with independently enumerated transition oracle."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
ORACLE = {
    "direct": "EXECUTE_AFTER_ORDINARY_GATES", "indirect": "EXECUTE_AFTER_ORDINARY_GATES",
    "capability_question": "EXPLAIN", "hypothetical": "EXPLAIN", "quoted_third_party": "EXPLAIN",
    "quoted_own_prior_for_analysis": "EXPLAIN", "prepare_only": "PREPARE", "explicit_negation": "EXPLAIN",
    "later_authenticated_adoption": "EXECUTE_AFTER_ORDINARY_GATES", "ambiguous_force": "ASK",
    "premise_false_or_unknown_control": "YIELD",
}
MUTATIONS = {
    "quote_boundary_removed": {"quoted_third_party": "EXECUTE_AFTER_ORDINARY_GATES"},
    "negation_dropped": {"prepare_only": "EXECUTE_AFTER_ORDINARY_GATES", "explicit_negation": "EXECUTE_AFTER_ORDINARY_GATES"},
    "turn_author_swapped": {"later_authenticated_adoption": "EXECUTE_AFTER_ORDINARY_GATES"},
    "stale_quoted_instruction_reused": {"quoted_own_prior_for_analysis": "EXECUTE_AFTER_ORDINARY_GATES"},
    "paraphrase_elevated_to_source": {"capability_question": "EXECUTE_AFTER_ORDINARY_GATES"},
    "premise_truth_confused_with_force": {"premise_false_or_unknown_control": "EXECUTE_AFTER_ORDINARY_GATES"},
}


def main():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    rows = json.loads((ROOT / "candidate.raw.json").read_text(encoding="utf-8"))
    actual = {row["case_id"]: row for row in rows}
    errors = []
    if set(actual) != set(ORACLE):
        errors.append("CASE_SET_MISMATCH")
    for cid, transition in ORACLE.items():
        row = actual.get(cid, {})
        if row.get("transition") != transition or row.get("errors") != []:
            errors.append(f"{cid}:ORACLE_MISMATCH")
    mutation_rejections = {}
    for name, cases_to_bad_transition in MUTATIONS.items():
        rejected = all(actual.get(cid, {}).get("transition") != bad for cid, bad in cases_to_bad_transition.items())
        mutation_rejections[name] = rejected
        if not rejected:
            errors.append(f"{name}:NOT_REJECTED")
    report = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "oracle_cases": len(ORACLE),
              "mutation_count": len(MUTATIONS), "mutation_rejections": mutation_rejections, "errors": errors,
              "claim_limit": "finite authored representation/transition contract only; no language, intent-truth, authority, human, runtime, or safety inference"}
    (ROOT / "audit.raw.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
