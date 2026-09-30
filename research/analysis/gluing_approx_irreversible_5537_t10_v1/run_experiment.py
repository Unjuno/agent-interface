"""T10 deterministic 180-row matrix with disjoint nested records."""
import hashlib
import json
from pathlib import Path

from candidate import evaluate

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "formal.jsonl"
EQUALITY = [
    {"name": "xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
    {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 0], [1, 1]], "spread": 0.0},
]
APPROX = [{**ctx, "spread": 0.5} for ctx in EQUALITY]
PARITY = [*EQUALITY[:2],
          {"name": "zx", "vars": ["z", "x"], "tuples": [[0, 1], [1, 0]], "spread": 1.0}]
INCOMPLETE = EQUALITY[:2]
CASES = {
    "exact": {"contexts": EQUALITY, "complete": True, "declared_spread": 0.0},
    "within_tolerance": {"contexts": APPROX, "complete": True, "declared_spread": 0.5},
    "beyond_tolerance": {"contexts": APPROX, "complete": True, "declared_spread": 0.5},
    "no_global_section": {"contexts": PARITY, "complete": True, "declared_spread": 1.0},
    "missing_context": {"contexts": INCOMPLETE, "complete": False, "declared_spread": 1.0},
}
TOLERANCES = (0.0, 0.25, 0.5, 1.0)
CONTRACTS = ("exact_only", "reversible_approximate",
             "explicit_allow_approximate_irreversible")
ACTIONS = ("reversible", "compensable", "irreversible")


def build_rows():
    rows = []
    for case, fixture in CASES.items():
        for tolerance in TOLERANCES:
            for contract in CONTRACTS:
                for action in ACTIONS:
                    decision_input = {"case": case, **fixture, "tolerance": tolerance,
                                      "contract": contract, "action": action}
                    row = {"decision_input": decision_input,
                           "decision_output": evaluate(decision_input)}
                    row["record_id"] = hashlib.sha256(json.dumps(
                        row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                    rows.append(row)
    return rows


def main():
    rows = build_rows()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                              for row in rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "cases": len(CASES), "tolerances": len(TOLERANCES),
                      "contracts": len(CONTRACTS), "actions": len(ACTIONS),
                      "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
