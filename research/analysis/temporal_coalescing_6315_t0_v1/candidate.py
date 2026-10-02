"""Deterministic projection candidate for Issue #6315 finite trace fixtures."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def project(case: dict, mode: str) -> list[int]:
    rows = case["rows"]
    if mode == "identity":
        return list(range(len(rows)))
    if mode == "exact_full_stutter":
        required = case["required"]
        edge_property = case["property"]["kind"] == "alarm_count"
        deadline_edge_property = case["property"]["kind"] == "deadline_event"
        kept: list[int] = []
        for i, row in enumerate(rows):
            is_edge = row.get("kind") == "alarm" or row.get("critical_edge")
            if edge_property and row.get("kind") == "alarm":
                continue
            previous_ready = rows[kept[-1]].get("ready") if kept else None
            edge_transition = (deadline_edge_property and i > 0
                               and row.get("ready") != rows[i - 1].get("ready"))
            if edge_transition and kept and rows[kept[-1]].get("critical_edge"):
                kept.pop()
            if kept and not is_edge and not (edge_property and rows[kept[-1]].get("kind") == "alarm") and not edge_transition and not any(
                    rows[j].get("kind") == "alarm" or rows[j].get("critical_edge")
                    for j in range(kept[-1] + 1, i + 1)) and all(
                    rows[kept[-1]][key] == row[key] for key in required):
                continue
            kept.append(i)
        return kept
    if mode == "latest_state_only":
        return [len(rows) - 1] if rows else []
    if mode == "retain_critical_edges":
        return [i for i, row in enumerate(rows) if row.get("critical_edge") or i == len(rows) - 1]
    raise ValueError(f"unknown mode: {mode}")


def main() -> int:
    inp, out = map(Path, sys.argv[1:3])
    fixture = json.loads(inp.read_text())
    records = []
    for case in fixture["cases"]:
        for mode in case["modes"]:
            records.append({"case_id": case["case_id"], "mode": mode,
                            "kept_indices": project(case, mode)})
    payload = {"schema": "temporal-coalescing-candidate.v1", "records": records}
    out.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
