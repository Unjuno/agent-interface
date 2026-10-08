"""Finite, no-model source-clause preservation construction for Issue #5951."""
import json
from pathlib import Path

ROOT = Path(__file__).parent


def candidate(case):
    """Check source coverage, authenticated supersession, support, and UNKNOWN."""
    source = {c["id"]: c for c in case["source"]}
    referenced = set()
    errors = []
    for item in case["derived"]:
        refs = item.get("source_ids", [])
        if item.get("status") == "unknown":
            if not refs or any(ref not in source for ref in refs):
                errors.append("UNKNOWN_SOURCE_INVALID")
            referenced.update(refs)
            continue
        if not refs:
            errors.append("UNSUPPORTED_DERIVATION")
            continue
        if any(ref not in source for ref in refs):
            errors.append("SOURCE_SPAN_MISMATCH")
            continue
        referenced.update(refs)
        supported_atoms = {atom for ref in refs for atom in source[ref].get("atoms", [])}
        if not set(item.get("covers", [])).issubset(supported_atoms):
            errors.append("UNSUPPORTED_DERIVATION")
        if item.get("status") == "preserved":
            required_atoms = {atom for ref in refs for atom in source[ref].get("atoms", [])}
            if not required_atoms.issubset(set(item.get("covers", []))):
                errors.append("CLAUSE_WEAKENED")
    superseded = {old for clause in case["source"] for old in clause.get("supersedes", [])}
    for clause in case["source"]:
        if clause["id"] in superseded:
            continue
        if clause.get("kind") == "ambiguous":
            if not any(i.get("status") == "unknown" and clause["id"] in i.get("source_ids", []) for i in case["derived"]):
                errors.append("AMBIGUITY_FORCED")
        elif clause["id"] not in referenced:
            errors.append("SOURCE_CLAUSE_OMITTED")
    # Supersession must be authenticated by a later turn and target an existing clause.
    for clause in case["source"]:
        for old in clause.get("supersedes", []):
            if (old not in source or clause["turn"] <= source[old]["turn"]
                    or not clause.get("authenticated") or not source[old].get("authenticated")):
                errors.append("INVALID_SUPERSESSION")
    return {"case_id": case["id"], "outcome": "PASS" if not errors else "FAIL", "errors": sorted(set(errors))}


def static_trace_baseline(case):
    """Fair minimal trace-to-targeted-test baseline; lacks turn-precedence semantics."""
    source = {c["id"]: c for c in case["source"]}
    linked = {sid for d in case["derived"] for sid in d.get("source_ids", []) if sid in source}
    # Static baseline creates one test obligation per clause and cannot retire old clauses.
    missing = sorted(c["id"] for c in case["source"] if c["id"] not in linked)
    unsupported = any(not d.get("source_ids") or any(s not in source for s in d.get("source_ids", [])) for d in case["derived"])
    return {"case_id": case["id"], "outcome": "FAIL" if missing or unsupported else "PASS", "missing_source_ids": missing, "unsupported": unsupported}


def main():
    frozen = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    rows = []
    for case in frozen["cases"]:
        rows.append({"case_id": case["id"], "expected": case["expected"], "candidate": candidate(case), "static_trace_baseline": static_trace_baseline(case)})
    (ROOT / "candidate.raw.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(rows, sort_keys=True))


if __name__ == "__main__":
    main()
