"""Independent raw-only auditor; deliberately duplicates, not imports, the oracle."""
import itertools
import json
import sys
from pathlib import Path

FACTORS = ("freshness", "lease", "responsibility", "delivery")


def tuples_for(row, strength):
    return {
        (indices, tuple(row[index] for index in indices))
        for indices in itertools.combinations(range(4), strength)
    }


def main():
    raw_path = Path(sys.argv[1])
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "constrained-interaction-5330-t0-raw-v1" or raw.get("factors") != list(FACTORS):
        errors.append("schema_or_factor_mismatch")
    designs = raw.get("designs", {})
    expected_names = {"OFAT", "PAIRWISE", "THREE_WAY", "EXHAUSTIVE"}
    if set(designs) != expected_names:
        errors.append("design_set_mismatch")
    rebuilt = {}
    for name, record in designs.items():
        rows = record.get("rows", [])
        if any(not isinstance(row, list) or len(row) != 4 or any(type(v) is not int or v not in (0, 1) for v in row) for row in rows):
            errors.append(f"invalid_row:{name}")
            continue
        if len({tuple(row) for row in rows}) != len(rows):
            errors.append(f"duplicate_row:{name}")
        pair = set().union(*(tuples_for(row, 2) for row in rows)) if rows else set()
        triple = set().union(*(tuples_for(row, 3) for row in rows)) if rows else set()
        ph = any(row[0] == 1 and row[1] == 1 for row in rows)
        th = any(row[0] == 1 and row[2] == 1 and row[3] == 1 for row in rows)
        observed = {
            "case_count": len(rows), "pair_coverage": len(pair), "triple_coverage": len(triple),
            "pair_hazard_detected": ph, "triple_hazard_detected": th,
        }
        if any(record.get(k) != v for k, v in observed.items()):
            errors.append(f"aggregate_mismatch:{name}")
        rebuilt[name] = observed
    if rebuilt.get("OFAT", {}).get("pair_hazard_detected") is not False or rebuilt.get("PAIRWISE", {}).get("pair_hazard_detected") is not True:
        errors.append("pair_detection_contrast_missing")
    if rebuilt.get("PAIRWISE", {}).get("pair_coverage") != 24:
        errors.append("pairwise_coverage_incomplete")
    if rebuilt.get("THREE_WAY", {}).get("triple_coverage") != 32 or rebuilt.get("THREE_WAY", {}).get("triple_hazard_detected") is not True:
        errors.append("three_way_coverage_or_detection_missing")
    if rebuilt.get("EXHAUSTIVE", {}).get("case_count") != 16:
        errors.append("exhaustive_baseline_wrong")
    if any(rebuilt.get(name, {}).get("case_count", 16) >= 16 for name in ("PAIRWISE", "THREE_WAY")):
        errors.append("no_case_reduction")
    output = {"status": "PASS_AUDIT" if not errors else "STOP_AUDIT_MISMATCH", "errors": errors, "rebuilt": rebuilt}
    print(json.dumps(output, sort_keys=True))
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
