#!/usr/bin/env python3
"""Finite global-section parity-cycle probe for Issue #5537 T4."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

OUT = Path(__file__).with_name("raw") / "formal.jsonl"
BASE = [
    {"name": "C_xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]]},
    {"name": "C_yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]]},
]
PARITY = {"name": "C_zx", "vars": ["z", "x"], "tuples": [[0, 1], [1, 0]]}
EQUALITY = {"name": "C_zx", "vars": ["z", "x"], "tuples": [[0, 0], [1, 1]]}


def solve(contexts, complete):
    domains = {v: set() for v in ("x", "y", "z")}
    for c in contexts:
        for tup in c["tuples"]:
            for v, val in zip(c["vars"], tup):
                domains[v].add(val)
    pairwise = True
    for a, b in itertools.combinations(contexts, 2):
        shared = set(a["vars"]) & set(b["vars"])
        for v in shared:
            pa = {t[a["vars"].index(v)] for t in a["tuples"]}
            pb = {t[b["vars"].index(v)] for t in b["tuples"]}
            pairwise &= pa == pb
    sections = []
    if complete:
        for values in itertools.product((0, 1), repeat=3):
            assignment = dict(zip(("x", "y", "z"), values))
            if all(tuple(assignment[v] for v in c["vars"]) in [tuple(t) for t in c["tuples"]] for c in contexts):
                sections.append(assignment)
    status = "UNKNOWN" if not complete else "GLOBAL_SECTION_CERTIFIED" if sections else "NO_GLOBAL_SECTION"
    return {"pairwise_compatible": bool(pairwise), "global_sections": sections, "status": status,
            "irreversible_admitted": status == "GLOBAL_SECTION_CERTIFIED"}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cases = [
        ("pairwise_compatible_parity_cycle", BASE + [PARITY], True),
        ("coherent_equality_control", BASE + [EQUALITY], True),
        ("missing_context_control", BASE, False),
    ]
    rows = []
    for case, contexts, complete in cases:
        row = {"case": case, "contexts": contexts, "complete": complete, **solve(contexts, complete)}
        row["record_id"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        rows.append(row)
    OUT.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "pairwise_cycle_status": rows[0]["status"],
                      "pairwise_cycle_sections": len(rows[0]["global_sections"]),
                      "coherent_control_sections": len(rows[1]["global_sections"]),
                      "missing_control_status": rows[2]["status"], "raw_path": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
