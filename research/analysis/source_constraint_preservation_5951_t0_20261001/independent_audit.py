"""Independent result adjudicator; intentionally does not import experiment.py."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
# Separately authored finite oracle, not read from each case's expected field.
ORACLE = {
    "exact_copy": ("PASS", set()),
    "paraphrase": ("PASS", set()),
    "omitted_prohibition": ("FAIL", {"SOURCE_CLAUSE_OMITTED"}),
    "weakened_conditional": ("FAIL", {"CLAUSE_WEAKENED"}),
    "invented_permission": ("FAIL", {"UNSUPPORTED_DERIVATION"}),
    "authenticated_supersession": ("PASS", set()),
    "genuine_ambiguity": ("PASS", set()),
    "source_span_mismatch": ("FAIL", {"SOURCE_SPAN_MISMATCH"}),
}


def main():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    results = json.loads((ROOT / "candidate.raw.json").read_text(encoding="utf-8"))
    by_id = {row["case_id"]: row for row in results}
    errors = []
    if set(by_id) != set(ORACLE):
        errors.append("CASE_SET_MISMATCH")
    for case in cases:
        cid = case["id"]
        expected_outcome, expected_errors = ORACLE[cid]
        actual = by_id.get(cid, {}).get("candidate", {})
        if actual.get("outcome") != expected_outcome:
            errors.append(f"{cid}:OUTCOME")
        if set(actual.get("errors", [])) != expected_errors:
            errors.append(f"{cid}:ERROR_CLASS")
        if case.get("expected") not in {"PASS", "PASS_UNKNOWN", "FAIL_OMISSION", "FAIL_WEAKENED", "FAIL_UNSUPPORTED", "FAIL_SOURCE"}:
            errors.append(f"{cid}:INVALID_CASE_EXPECTATION")
    report = {"status": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT", "independent_oracle_cases": len(ORACLE), "errors": errors}
    (ROOT / "audit.raw.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
