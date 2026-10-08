"""Corrected static trace baseline that permits linked UNKNOWN ambiguity."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXPECTED = {
    "exact_copy": "PASS", "paraphrase": "PASS", "omitted_prohibition": "FAIL",
    "weakened_conditional": "FAIL", "invented_permission": "FAIL",
    "authenticated_supersession": "FAIL", "genuine_ambiguity": "PASS",
    "source_span_mismatch": "FAIL",
}


def score(case):
    sources = {c["id"]: c for c in case["source"]}
    errors = set()
    covered = {sid: set() for sid in sources}
    unknown_ids = set()
    for derived in case["derived"]:
        refs = derived.get("source_ids", [])
        if any(ref not in sources for ref in refs):
            errors.add("SOURCE_SPAN_MISMATCH")
            continue
        atoms = set(derived.get("covers", []))
        supported = {atom for ref in refs for atom in sources[ref].get("atoms", [])}
        if not atoms.issubset(supported):
            errors.add("UNSUPPORTED_DERIVATION")
        for ref in refs:
            covered[ref].update(atoms & set(sources[ref].get("atoms", [])))
            if derived.get("status") == "unknown":
                if sources[ref].get("kind") != "ambiguous":
                    errors.add("UNJUSTIFIED_UNKNOWN")
                else:
                    unknown_ids.add(ref)
    for sid, source in sources.items():
        if sid in unknown_ids and source.get("kind") == "ambiguous":
            continue
        if not set(source.get("atoms", [])).issubset(covered[sid]):
            errors.add("SOURCE_CLAUSE_NOT_TESTED")
    return {"outcome": "PASS" if not errors else "FAIL", "errors": sorted(errors)}


def main():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    rows = [{"case_id": c["id"], "expected": EXPECTED[c["id"]], "baseline": score(c)} for c in cases]
    mismatches = [r["case_id"] for r in rows if r["expected"] != r["baseline"]["outcome"]]
    report = {"status": "PASS_BASELINE_CONSTRUCTION" if not mismatches else "FAIL_BASELINE_CONSTRUCTION", "mismatches": mismatches, "rows": rows}
    (Path(__file__).parent / "baseline_v3.raw.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not mismatches else 1)


if __name__ == "__main__":
    main()
