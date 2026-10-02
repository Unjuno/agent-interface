"""Stronger static clause-to-targeted-test baseline; no turn precedence."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def score(case):
    sources = {c["id"]: c for c in case["source"]}
    errors = set()
    covered = {sid: set() for sid in sources}
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
        if derived.get("status") == "unknown" and any(sources[ref].get("kind") != "ambiguous" for ref in refs):
            errors.add("UNJUSTIFIED_UNKNOWN")
    for sid, source in sources.items():
        if not set(source.get("atoms", [])).issubset(covered[sid]):
            errors.add("SOURCE_CLAUSE_NOT_TESTED")
    return {"outcome": "PASS" if not errors else "FAIL", "errors": sorted(errors)}


def main():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    rows = [{"case_id": c["id"], "baseline": score(c)} for c in cases]
    (Path(__file__).parent / "baseline.raw.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(rows, sort_keys=True))


if __name__ == "__main__":
    main()
