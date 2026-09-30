"""One-shot T12 144-row numeric/scope decision matrix."""
import hashlib
import json
from pathlib import Path

from candidate import evaluate

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "formal.jsonl"
EXACT = [{"left": "x", "right": "y", "target_ticks": 0},
         {"left": "y", "right": "z", "target_ticks": 0},
         {"left": "z", "right": "x", "target_ticks": 0}]
NEAR = [*EXACT[:2], {"left": "z", "right": "x", "target_ticks": 4}]
FAR = [*EXACT[:2], {"left": "z", "right": "x", "target_ticks": 8}]
CASES = {"exact_cycle": (EXACT, True), "near_cycle": (NEAR, True),
         "far_cycle": (FAR, True), "missing_context": (NEAR[:2], False)}
TOLERANCES = (0, 1, 2, 4)
CONTRACTS = ("exact_only", "reversible_approximate",
             "explicit_allow_approximate_irreversible")
ACTIONS = ("reversible", "compensable", "irreversible")


def build_rows():
    rows = []
    for case, (relations, complete) in CASES.items():
        for tolerance in TOLERANCES:
            for contract in CONTRACTS:
                for action in ACTIONS:
                    decision_input = {"case": case, "relations": relations, "complete": complete,
                                      "tolerance_ticks": tolerance, "contract": contract,
                                      "action": action}
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
