#!/usr/bin/env python3
"""Independent raw-only oracle for #7165 A02; does not import candidate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "runs" / "candidate" / "raw.jsonl"
AUDIT = ROOT / "runs" / "auditor" / "audit.json"
REQUIRED = {"title", "parent"}
VALID = {"A", "B"}


def oracle(pair: dict[str, str]) -> str:
    first = pair["title"]
    second = pair["parent"]
    if first in VALID and second == first:
        return first
    return "UNKNOWN"


def expected_route(row: dict) -> str:
    complete = len(row["requirement"]) == len(REQUIRED) and set(row["requirement"]) == REQUIRED
    provenance_ok = row["generation_match"] is True and row["source_valid"] is True
    reads_current = all(row["read_status"].get(name) == "CURRENT" for name in REQUIRED)
    values_agree = oracle(row["fresh"]) in VALID
    if complete and provenance_ok and reads_current and values_agree:
        return "targeted_current_complete"
    return "fresh_full_fallback"


def main() -> None:
    lines = RAW.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    unique: set[str] = set()
    route_counts: dict[str, int] = {}
    for idx, line in enumerate(lines):
        row = json.loads(line)
        case = {key: row[key] for key in (
            "requirement", "generation_match", "source_valid", "read_status", "fresh"
        )}
        signature = json.dumps(case, sort_keys=True, separators=(",", ":"))
        if signature in unique:
            errors.append(f"duplicate state row {idx}")
        unique.add(signature)
        want_route = expected_route(row)
        want_decision = oracle(row["fresh"])
        route_counts[row["route"]] = route_counts.get(row["route"], 0) + 1
        if row["route"] != want_route:
            errors.append(f"route mismatch row {idx}: {row['route']} != {want_route}")
        if row["decision"] != want_decision:
            errors.append(f"decision mismatch row {idx}: {row['decision']} != {want_decision}")
    # Independently derive the finite product: 4 requirement shapes, two
    # booleans, 4^2 read statuses, and 3^2 full-observation values.
    expected_count = 4 * 2 * 2 * (4 ** 2) * (3 ** 2)
    if len(lines) != expected_count or len(unique) != expected_count:
        errors.append(f"coverage mismatch: {len(unique)} unique of {expected_count}")
    controls = {
        "missing_required_cue_falls_back": expected_route({
            "requirement": ["title"], "generation_match": True, "source_valid": True,
            "read_status": {"title": "CURRENT", "parent": "CURRENT"},
        }) == "fresh_full_fallback",
        "stale_context_falls_back": expected_route({
            "requirement": ["title", "parent"], "generation_match": False,
            "source_valid": True, "read_status": {"title": "CURRENT", "parent": "CURRENT"},
        }) == "fresh_full_fallback",
        "wrong_source_falls_back": expected_route({
            "requirement": ["title", "parent"], "generation_match": True,
            "source_valid": False, "read_status": {"title": "CURRENT", "parent": "CURRENT"},
        }) == "fresh_full_fallback",
        "stale_read_falls_back": expected_route({
            "requirement": ["title", "parent"], "generation_match": True,
            "source_valid": True, "read_status": {"title": "STALE", "parent": "CURRENT"},
        }) == "fresh_full_fallback",
        "contradiction_refuses": oracle({"title": "A", "parent": "B"}) == "UNKNOWN",
        "missing_current_cue_refuses": oracle({"title": "A", "parent": "MISSING"}) == "UNKNOWN",
    }
    if not all(controls.values()):
        errors.append("a corruption/mutation control was not rejected")
    result = {
        "rows": len(lines), "unique_rows": len(unique), "route_counts": route_counts,
        "mutation_controls": controls, "errors": errors,
        "audit": "PASS_RAW_RECONSTRUCTION" if not errors else "FAIL",
        "scope": "finite contract fixture only",
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
