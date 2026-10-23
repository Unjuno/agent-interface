#!/usr/bin/env python3
"""Finite contract candidate for #7165 A02; no native/runtime calls."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

OUT = Path(__file__).parent / "runs" / "candidate" / "raw.jsonl"
CUES = ("title", "parent")
VALUES = ("A", "B", "MISSING")
READ_STATUS = ("CURRENT", "MISSING", "STALE", "WRONG_SOURCE")


def full_revalidate(readings: dict[str, str]) -> str:
    a, b = readings["title"], readings["parent"]
    return a if a in ("A", "B") and b == a else "UNKNOWN"


def memory_gated(requirement: tuple[str, ...], memory_generation: int,
                 current_generation: int, source_valid: bool,
                 read_status: dict[str, str], fresh: dict[str, str]) -> tuple[str, str]:
    usable = (
        tuple(sorted(requirement)) == tuple(sorted(CUES))
        and memory_generation == current_generation
        and source_valid
    )
    if usable and all(read_status[key] == "CURRENT" for key in CUES):
        # Under the frozen contract, CURRENT means the cue is bound to this
        # source and generation, so it equals the paired fresh fixture value.
        a, b = fresh["title"], fresh["parent"]
        if a in ("A", "B") and b == a:
            return a, "targeted_current_complete"
    return full_revalidate(fresh), "fresh_full_fallback"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with OUT.open("w", encoding="utf-8") as stream:
        # 4 requirement shapes x 2 generations x 2 source states x
        # 16 read-status pairs x 9 fresh-value pairs = 2,304 cases.
        requirements = ((), ("title",), ("parent",), CUES)
        for req, gen_match, source_valid, read_statuses, fresh_values in itertools.product(
            requirements, (False, True), (False, True),
            itertools.product(READ_STATUS, repeat=2),
            itertools.product(VALUES, repeat=2),
        ):
            current_generation = 7
            memory_generation = current_generation if gen_match else current_generation - 1
            status = dict(zip(CUES, read_statuses))
            fresh = dict(zip(CUES, fresh_values))
            decision, route = memory_gated(
                req, memory_generation, current_generation, source_valid, status, fresh
            )
            row = {
                "requirement": list(req), "generation_match": gen_match,
                "source_valid": source_valid, "read_status": status,
                "fresh": fresh, "decision": decision, "route": route,
            }
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            rows += 1
    repo = Path(__file__).parents[3]
    print(json.dumps({"rows": rows, "raw": str(OUT.relative_to(repo))}, sort_keys=True))


if __name__ == "__main__":
    main()
