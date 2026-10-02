"""Finite source-row projection candidate for Issue #5887 A02."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ARMS = ("identity", "exact_timed_stutter", "semantic_only", "latest_only")
PREDICATES = ("warning_count", "commit_ack_by_deadline", "authority_changes")


def _indices(rows: list[dict[str, Any]], arm: str) -> list[int]:
    if arm == "identity":
        return list(range(len(rows)))
    if arm == "latest_only":
        return [len(rows) - 1]
    kept: list[int] = []
    for i, row in enumerate(rows):
        if not kept:
            kept.append(i)
            continue
        prev = rows[kept[-1]]
        if arm == "exact_timed_stutter":
            same = row == prev
        elif arm == "semantic_only":
            same = row["props"] == prev["props"] and row["generation"] == prev["generation"]
        else:
            raise ValueError(f"unknown arm: {arm}")
        if not same:
            kept.append(i)
    return kept


def _values(rows: list[dict[str, Any]], deadline: int) -> dict[str, Any]:
    warning_count = sum(edge["kind"] == "warning" for row in rows for edge in row["edges"])
    if any(row["t_ms"] is None for row in rows):
        by_deadline: Any = "UNKNOWN"
    else:
        by_deadline = any(
            edge["kind"] == "commit_ack" and row["t_ms"] <= deadline
            for row in rows for edge in row["edges"]
        )
    authority_changes = sum(a["generation"] != b["generation"] for a, b in zip(rows, rows[1:]))
    return {
        "warning_count": warning_count,
        "commit_ack_by_deadline": by_deadline,
        "authority_changes": authority_changes,
    }


def build(fixture: dict[str, Any]) -> dict[str, Any]:
    out_rows = []
    for trace in fixture["traces"]:
        rows = trace["rows"]
        full = _values(rows, fixture["deadline_ms"])
        for arm in ARMS:
            kept = _indices(rows, arm)
            projected = [rows[i] for i in kept]
            vals = _values(projected, fixture["deadline_ms"])
            verdicts = {}
            for name in PREDICATES:
                before, after = full[name], vals[name]
                if before == "UNKNOWN" or after == "UNKNOWN":
                    status = "UNKNOWN"
                else:
                    status = "PRESERVED" if before == after else "NOT_PRESERVED"
                verdicts[name] = {
                    "full": before,
                    "projected": after,
                    "status": status,
                    "dropped_source_indices": [i for i in range(len(rows)) if i not in kept],
                }
            out_rows.append({
                "trace_id": trace["id"],
                "arm": arm,
                "source_indices": kept,
                "projected_rows": projected,
                "predicates": verdicts,
            })
    return {"schema": "temporal-preservation-5887-a03-raw-v1", "input": fixture, "rows": out_rows}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: candidate.py FIXTURE.json RAW.json", file=sys.stderr)
        return 2
    fixture = json.loads(Path(argv[1]).read_text())
    Path(argv[2]).write_text(json.dumps(build(fixture), sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
