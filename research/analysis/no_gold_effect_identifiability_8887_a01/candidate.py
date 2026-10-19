"""Emit only the no-gold observations for #8887 common-mode control A01."""
import json
import sys
from pathlib import Path


ALLOCATION = "8887-common-mode-observational-equivalence-a01-20261012-01"
BITS = "00001111"
CHECKERS = ("file", "app_readback", "visual_receipt", "shared_parser")


def build_record():
    rows = [
        {"row_id": f"r{i:02d}", "outputs": {name: int(bit) for name in CHECKERS}}
        for i, bit in enumerate(BITS)
    ]
    pair_agreement = {}
    for i, left in enumerate(CHECKERS):
        for right in CHECKERS[i + 1:]:
            pair_agreement[f"{left}|{right}"] = sum(
                row["outputs"][left] == row["outputs"][right] for row in rows
            ) / len(rows)
    return {
        "schema": "no_gold_common_mode_control_v1",
        "allocation": ALLOCATION,
        "checker_ids": list(CHECKERS),
        "rows": rows,
        "observed_prevalence": {
            name: sum(row["outputs"][name] for row in rows) / len(rows)
            for name in CHECKERS
        },
        "pairwise_agreement": pair_agreement,
        "no_gold_disposition": "UNIDENTIFIABLE_WITHOUT_INDEPENDENCE_EVIDENCE",
        "accuracy_estimate": None,
        "confidence_claim": None,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    record = build_record()
    path = Path(sys.argv[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("candidate_written")


if __name__ == "__main__":
    main()
