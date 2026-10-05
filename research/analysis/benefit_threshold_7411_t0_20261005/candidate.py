"""Frozen method candidate: empirical 50% worthwhile-choice crossing."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE / "INPUT.json"
OUTPUT = HERE / "CANDIDATE.json"
ALLOWED = {"worthwhile", "not_worthwhile", "indifferent", "missing"}


def estimate(data):
    rows = data["records"]
    if len({row["trial_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate trial id")
    conditions = sorted({row["condition"] for row in rows})
    result = {}
    for condition in conditions:
        subset = [r for r in rows if r["condition"] == condition]
        gates = {r["correctness_gate"] for r in subset}
        if len(gates) != 1 or type(next(iter(gates))) is not bool:
            result[condition] = {"status": "UNKNOWN_INVALID_GATE"}
            continue
        cells = []
        for dose in data["dose_levels_ms"]:
            cell = [r for r in subset if r["dose_ms_saved"] == dose]
            if any(r["choice"] not in ALLOWED for r in cell):
                raise ValueError("unknown response category")
            valid = [r for r in cell if r["choice"] in ("worthwhile", "not_worthwhile")]
            yes = sum(r["choice"] == "worthwhile" for r in valid)
            cells.append({"dose_ms_saved": dose, "n_valid": len(valid),
                          "n_worthwhile": yes,
                          "proportion": round(yes / len(valid), 6) if valid else None})
        if gates == {False}:
            result[condition] = {"status": "INELIGIBLE_CORRECTNESS_GATE",
                                 "cells": cells, "threshold_bracket_ms": None}
            continue
        if any(c["n_valid"] < data["minimum_valid_per_dose"] for c in cells):
            result[condition] = {"status": "UNKNOWN_INSUFFICIENT_SUPPORT",
                                 "cells": cells, "threshold_bracket_ms": None}
            continue
        crossing = next((i for i, c in enumerate(cells) if c["proportion"] >= 0.5), None)
        if crossing is None:
            status, bracket = "UNKNOWN_NO_CROSSING", None
        elif crossing == 0:
            status, bracket = "CROSSED_AT_MIN_TESTED_DOSE", [None, cells[0]["dose_ms_saved"]]
        else:
            status = "THRESHOLD_BRACKETED"
            bracket = [cells[crossing - 1]["dose_ms_saved"], cells[crossing]["dose_ms_saved"]]
        result[condition] = {"status": status, "cells": cells,
                             "threshold_bracket_ms": bracket}
    return result


def main():
    raw = INPUT.read_bytes()
    data = json.loads(raw)
    output = {"input_sha256": hashlib.sha256(raw).hexdigest(),
              "estimator": "first-tested-dose-with-at-least-50%-worthwhile-choices",
              "results": estimate(data)}
    encoded = (json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n").encode()
    OUTPUT.write_bytes(encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
