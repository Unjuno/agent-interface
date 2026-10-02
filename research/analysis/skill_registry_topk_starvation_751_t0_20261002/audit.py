import argparse
import hashlib
import json
from pathlib import Path


METHODS = ("SEMANTIC_TOP_K_THEN_FILTER", "FILTER_THEN_RANK", "BOUNDED_WIDENING")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_status(selected, unresolved, partial, total):
    if selected:
        return "SELECTED"
    if unresolved:
        return "UNKNOWN_APPLICABILITY_UNRESOLVED"
    if partial:
        return "UNKNOWN_NOT_FOUND_WITHIN_BUDGET"
    return "NONE_PROVEN_APPLICABLE"


def reconstruct(fixture):
    result = {}
    k, budget = fixture["retrieval_k"], fixture["scan_budget"]
    for case in fixture["cases"]:
        skills = [{"id": row[0], "eligibility": row[1], "rank": i + 1}
                  for i, row in enumerate(case["skills"])]
        all_allowed = [s for s in skills if s["eligibility"] == "ALLOW"]
        top = skills[:k]
        top_allowed = [s for s in top if s["eligibility"] == "ALLOW"]
        prefix = skills[:min(budget, len(skills))]
        prefix_allowed = [s for s in prefix if s["eligibility"] == "ALLOW"]
        rows = {
            "SEMANTIC_TOP_K_THEN_FILTER": (top_allowed,
                any(s["eligibility"] == "UNKNOWN" for s in top), len(top),
                len(top) == k, len(top_allowed)),
            "FILTER_THEN_RANK": (all_allowed[:k],
                any(s["eligibility"] == "UNKNOWN" for s in skills), len(skills),
                False, min(k, len(all_allowed))),
            "BOUNDED_WIDENING": (prefix_allowed[:k],
                any(s["eligibility"] == "UNKNOWN" for s in prefix), len(prefix),
                len(prefix) < len(skills), min(k, len(prefix_allowed)))
        }
        result[case["case_id"]] = {}
        for method, (selected, unknown, checks, partial, cards) in rows.items():
            result[case["case_id"]][method] = {
                "selected": [s["id"] for s in selected],
                "status": expected_status(selected, unknown, partial, len(skills)),
                "metadata_checks": checks,
                "cards_returned": cards
            }
    return result


def audit(fixture, raw, fixture_path, candidate_path):
    errors = []
    if raw.get("fixture_id") != fixture.get("fixture_id"):
        errors.append("fixture_id_mismatch")
    if raw.get("fixture_sha256") != sha256(fixture_path):
        errors.append("fixture_hash_mismatch")
    if raw.get("candidate_sha256") != sha256(candidate_path):
        errors.append("candidate_hash_mismatch")
    if raw.get("retrieval_k") != fixture.get("retrieval_k"):
        errors.append("retrieval_k_mismatch")
    if raw.get("scan_budget") != fixture.get("scan_budget"):
        errors.append("scan_budget_mismatch")
    expected = reconstruct(fixture)
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != len(fixture["cases"]):
        errors.append("case_count_mismatch")
        rows = rows if isinstance(rows, list) else []
    actual_ids = [r.get("case_id") for r in rows if isinstance(r, dict)]
    if actual_ids != list(expected):
        errors.append("case_identity_or_order_mismatch")
    for row in rows:
        if not isinstance(row, dict) or row.get("case_id") not in expected:
            errors.append("unknown_case_row")
            continue
        case_id = row["case_id"]
        methods = row.get("methods")
        if not isinstance(methods, dict) or set(methods) != set(METHODS):
            errors.append(f"method_set_mismatch:{case_id}")
            continue
        for method in METHODS:
            if methods.get(method) != expected[case_id][method]:
                errors.append(f"reconstruction_mismatch:{case_id}:{method}")
            for skill_id in methods.get(method, {}).get("selected", []):
                truth = next((x[1] for x in fixture["cases"]
                              if x["case_id"] == case_id
                              for x in x["skills"] if x[0] == skill_id), None)
                if truth != "ALLOW":
                    errors.append(f"unsafe_selection:{case_id}:{method}:{skill_id}")
    status = "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT"
    return {"status": status, "errors": errors,
            "case_count": len(fixture["cases"]), "method_count": len(METHODS),
            "independent_reconstruction": True,
            "fixture_sha256": sha256(fixture_path),
            "candidate_sha256": sha256(candidate_path),
            "raw_sha256": hashlib.sha256(
                json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture_path, candidate_path = Path(args.fixture), Path(args.candidate)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    result = audit(fixture, raw, fixture_path, candidate_path)
    Path(args.out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "METHOD_PASS_SCOPED" else 1)


if __name__ == "__main__":
    main()

