"""Exhaustive T0 candidate for Issue #5305; stdlib only."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path


ATOMS = (
    {"id": "s1", "sign": "support", "fresh": True, "group": "g1"},
    {"id": "s1dup", "sign": "support", "fresh": True, "group": "g1"},
    {"id": "s2", "sign": "support", "fresh": True, "group": "g2"},
    {"id": "r1", "sign": "refute", "fresh": True, "group": "g3"},
    {"id": "sold", "sign": "support", "fresh": False, "group": "g4"},
)


def candidate(rows):
    fresh = [row for row in rows if row["fresh"]]
    support = {row["group"] for row in fresh if row["sign"] == "support"}
    refute = {row["group"] for row in fresh if row["sign"] == "refute"}
    if support and refute:
        status = "CONFLICT"
    elif support:
        status = "PASS"
    elif refute:
        status = "FAIL"
    else:
        status = "UNCERTAIN"
    return {"status": status, "support_groups": sorted(support),
            "refute_groups": sorted(refute), "stale_count": sum(not r["fresh"] for r in rows)}


def lossy_ternary(rows):
    state = "UNCERTAIN"
    for row in rows:
        if not row["fresh"]:
            continue
        sign = "PASS" if row["sign"] == "support" else "FAIL"
        if state == "UNCERTAIN":
            state = sign
        elif state != sign:
            state = "UNCERTAIN"
    return state


def main():
    cases = []
    for size in range(1, len(ATOMS) + 1):
        for rows in itertools.combinations(ATOMS, size):
            cases.append({"ids": [r["id"] for r in rows], "candidate": candidate(rows),
                          "ternary": lossy_ternary(rows)})
    payload = {"schema": "conflict-ledger-5305-t0-v1", "atom_count": len(ATOMS),
               "case_count": len(cases), "cases": cases}
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    out = Path(__file__).parent / "raw.json"
    out.write_bytes(raw)
    (Path(__file__).parent / "raw.sha256").write_text(hashlib.sha256(raw).hexdigest() + "  raw.json\n")
    counts = {}
    collapsed = 0
    for case in cases:
        status = case["candidate"]["status"]
        counts[status] = counts.get(status, 0) + 1
        if status == "CONFLICT" and case["ternary"] == "UNCERTAIN":
            collapsed += 1
    print(json.dumps({"outcome": "CANDIDATE_COMPLETE", "case_count": len(cases),
                      "candidate_status_counts": counts, "fresh_conflicts_collapsed_by_ternary": collapsed,
                      "raw_sha256": hashlib.sha256(raw).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
