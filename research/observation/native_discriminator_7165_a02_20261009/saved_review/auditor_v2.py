#!/usr/bin/env python3
"""Post-hoc read-only reconstruction; does not rerun candidate or change first HOLD."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "runs" / "candidate" / "raw.jsonl"
OUT = ROOT / "saved_review" / "AUDIT_V2.json"
REQUIRED = {"title", "parent"}
VALID = {"A", "B"}
STATUSES = {"CURRENT", "MISSING", "STALE", "WRONG_SOURCE"}


def fresh_decision(pair: dict[str, str]) -> str:
    title, parent = pair["title"], pair["parent"]
    return title if title in VALID and parent == title else "UNKNOWN"


def expected_path(row: dict) -> str:
    complete = len(row["requirement"]) == 2 and set(row["requirement"]) == REQUIRED
    current = row["generation_match"] is True and row["source_valid"] is True
    current_reads = set(row["read_status"]) == REQUIRED and all(
        row["read_status"][cue] == "CURRENT" for cue in REQUIRED
    )
    resolved = fresh_decision(row["fresh"]) in VALID
    return "targeted_current_complete" if complete and current and current_reads and resolved else "fresh_full_fallback"


def main() -> None:
    lines = RAW.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    seen: set[str] = set()
    route_counts: dict[str, int] = {}
    for index, text in enumerate(lines):
        row = json.loads(text)
        identity = json.dumps({key: row[key] for key in (
            "requirement", "generation_match", "source_valid", "read_status", "fresh"
        )}, sort_keys=True, separators=(",", ":"))
        if identity in seen:
            errors.append(f"duplicate input state at row {index}")
        seen.add(identity)
        wanted_path = expected_path(row)
        wanted_decision = fresh_decision(row["fresh"])
        route_counts[row["route"]] = route_counts.get(row["route"], 0) + 1
        if row["route"] != wanted_path:
            errors.append(f"path mismatch at row {index}")
        if row["decision"] != wanted_decision:
            errors.append(f"decision mismatch at row {index}")
        if row["route"] == "targeted_current_complete" and wanted_decision not in VALID:
            errors.append(f"nonunique targeted bind at row {index}")

    expected_total = 4 * 2 * 2 * (len(STATUSES) ** 2) * (3 ** 2)
    if len(lines) != expected_total or len(seen) != expected_total:
        errors.append(f"state coverage {len(seen)}/{expected_total}")

    valid_pair = {"title": "A", "parent": "A"}
    base = {"requirement": ["title", "parent"], "generation_match": True,
            "source_valid": True, "read_status": {"title": "CURRENT", "parent": "CURRENT"},
            "fresh": valid_pair, "route": "targeted_current_complete", "decision": "A"}
    mutations = {}
    for name, edit in {
        "incomplete_requirement_accepted": lambda r: r.update(requirement=["title"]),
        "stale_generation_accepted": lambda r: r.update(generation_match=False),
        "wrong_source_accepted": lambda r: r.update(source_valid=False),
        "stale_read_accepted": lambda r: r["read_status"].update(title="STALE"),
        "missing_cue_bound": lambda r: r.update(fresh={"title": "A", "parent": "MISSING"}, decision="A"),
        "contradictory_cues_bound": lambda r: r.update(fresh={"title": "A", "parent": "B"}, decision="A"),
        "wrong_identity_decision": lambda r: r.update(decision="B"),
    }.items():
        changed = json.loads(json.dumps(base))
        edit(changed)
        mutations[name] = changed["route"] != expected_path(changed) or changed["decision"] != fresh_decision(changed["fresh"])
    if not all(mutations.values()):
        errors.append("a mutation control was not detected")

    result = {
        "audit": "PASS_RAW_RECONSTRUCTION_V2" if not errors else "FAIL_RAW_RECONSTRUCTION_V2",
        "rows": len(lines), "unique_states": len(seen), "expected_states": expected_total,
        "routes": route_counts, "mutation_controls_detected": mutations,
        "errors": errors,
        "scope": "read-only saved raw reconstruction; original HOLD_AUDITOR_RUNTIME_ERROR remains",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
