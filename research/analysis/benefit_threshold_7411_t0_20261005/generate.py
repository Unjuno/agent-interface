"""Create frozen synthetic paired-choice records; no user data or I/O beyond files."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOSES = [0, 50, 100, 150, 200]
SEED = 7411


def main():
    rows = []
    specs = {
        "planner_boundary": [50] * 20 + [100] * 20 + [150] * 20 + [200] * 20,
        "local_processing": [100] * 20 + [150] * 20 + [200] * 40,
        "correctness_regression": [0] * 80,
        "sparse_support": [50, 100, 150, 200, 200, 200],
    }
    for condition, thresholds in specs.items():
        for person, threshold in enumerate(thresholds):
            for dose_index, dose in enumerate(DOSES):
                token = (SEED + person * 31 + dose_index * 17 + len(condition) * 7) % 101
                if token in (0, 1):
                    choice = "missing"
                elif token in (2, 3, 4):
                    choice = "indifferent"
                else:
                    positive = dose >= threshold
                    if token in (5, 6):
                        positive = not positive
                    choice = "worthwhile" if positive else "not_worthwhile"
                rows.append({
                    "trial_id": f"{condition}:{person}:{dose}",
                    "condition": condition,
                    "participant": person,
                    "dose_ms_saved": dose,
                    "choice": choice,
                    "correctness_gate": condition != "correctness_regression",
                })
    raw = {"schema": "synthetic-paired-choice-v1", "seed": SEED,
           "dose_levels_ms": DOSES, "minimum_valid_per_dose": 20,
           "records": rows}
    data = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (HERE / "INPUT.json").write_bytes(data)
    print(json.dumps({"input_sha256": hashlib.sha256(data).hexdigest(),
                      "records": len(rows), "seed": SEED}, sort_keys=True))


if __name__ == "__main__":
    main()
