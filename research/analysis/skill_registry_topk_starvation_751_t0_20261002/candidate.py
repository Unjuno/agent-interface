import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(selected, unresolved, exhausted, scanned, total):
    if selected:
        return "SELECTED"
    if unresolved:
        return "UNKNOWN_APPLICABILITY_UNRESOLVED"
    if exhausted and scanned < total:
        return "UNKNOWN_NOT_FOUND_WITHIN_BUDGET"
    return "NONE_PROVEN_APPLICABLE"


def run(fixture):
    k = fixture["retrieval_k"]
    budget = fixture["scan_budget"]
    output = {"fixture_id": fixture["fixture_id"], "retrieval_k": k,
              "scan_budget": budget, "cases": []}
    for case in fixture["cases"]:
        skills = [{"skill_id": x[0], "eligibility": x[1], "rank": i + 1}
                  for i, x in enumerate(case["skills"])]
        by_method = {}

        # Fixed semantic shortlist, followed by the same hard gate.
        shortlist = skills[:k]
        eligible = [s for s in shortlist if s["eligibility"] == "ALLOW"]
        unresolved = any(s["eligibility"] == "UNKNOWN" for s in shortlist)
        by_method["SEMANTIC_TOP_K_THEN_FILTER"] = {
            "selected": [s["skill_id"] for s in eligible],
            "status": classify(eligible, unresolved, len(shortlist) == k,
                               len(shortlist), len(skills)),
            "metadata_checks": len(shortlist), "cards_returned": len(eligible)}

        # Exact applicability scan first, then semantic ranking among allowed rows.
        allowed = [s for s in skills if s["eligibility"] == "ALLOW"]
        unresolved_all = any(s["eligibility"] == "UNKNOWN" for s in skills)
        by_method["FILTER_THEN_RANK"] = {
            "selected": [s["skill_id"] for s in allowed[:k]],
            "status": classify(allowed[:k], unresolved_all, False,
                               len(skills), len(skills)),
            "metadata_checks": len(skills), "cards_returned": min(k, len(allowed))}

        # Widen the semantic prefix until k valid cards or the fixed scan budget.
        scanned = skills[:min(budget, len(skills))]
        allowed_scanned = [s for s in scanned if s["eligibility"] == "ALLOW"]
        unresolved_scanned = any(s["eligibility"] == "UNKNOWN" for s in scanned)
        complete = len(scanned) == len(skills)
        selected_widened = allowed_scanned[:k]
        by_method["BOUNDED_WIDENING"] = {
            "selected": [s["skill_id"] for s in selected_widened],
            "status": classify(selected_widened, unresolved_scanned,
                               not complete, len(scanned), len(skills)),
            "metadata_checks": len(scanned), "cards_returned": len(selected_widened)}
        output["cases"].append({"case_id": case["case_id"], "methods": by_method})
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture_path = Path(args.fixture)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw = run(fixture)
    raw["fixture_sha256"] = sha256(fixture_path)
    raw["candidate_sha256"] = sha256(__file__)
    Path(args.out).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8")
    print(json.dumps({"status": "PASS_CANDIDATE_SHAPE", "case_count": len(raw["cases"]),
                      "fixture_sha256": raw["fixture_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()

