"""Frozen finite policy matrix runner; writes raw JSONL once."""
import hashlib
import itertools
import json
from pathlib import Path

from candidate import solve

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "formal.jsonl"
EQ = [
    {"name": "xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
]
PARITY = [*EQ[:2], {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 1], [1, 0]], "spread": 1.0}]
WIDE = [{**c, "spread": 0.5} for c in EQ]
MISSING = EQ[:2]


def main():
    cases = [
        ("exact", EQ, True, 0.0),
        ("within_tolerance", WIDE, True, 0.5),
        ("beyond_tolerance", WIDE, True, 0.25),
        ("parity_empty", PARITY, True, 1.0),
        ("missing_context", MISSING, False, 1.0),
    ]
    policies = [
        ("exact_only", False),
        ("approx_reversible_only", False),
        ("explicit_approx_irreversible_contract", True),
    ]
    rows = []
    for case, contexts, complete, spread in cases:
        for tolerance in (0.0, 0.5, 1.0):
            for policy, override in policies:
                for action in ("reversible", "compensable", "irreversible"):
                    result = solve(contexts, complete, tolerance, action, override)
                    row = {
                        "case": case,
                        "contexts": contexts,
                        "complete": complete,
                        "declared_spread": spread,
                        "tolerance": tolerance,
                        "policy": policy,
                        "allow_approx_irreversible": override,
                        **result,
                    }
                    row["record_id"] = hashlib.sha256(
                        json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
                    ).hexdigest()
                    rows.append(row)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n"
                              for r in rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "cases": len(cases), "policies": len(policies),
                      "actions": 3, "tolerances": 3,
                      "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
