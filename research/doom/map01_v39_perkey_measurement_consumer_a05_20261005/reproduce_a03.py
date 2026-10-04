"""Read-only in-memory reproduction of A03 cross-row identity aliasing."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
A03 = HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005"
sys.path.insert(0, str(A03))
import audit as a03_audit  # noqa: E402
import candidate as a03_candidate  # noqa: E402

EVENTS = [json.loads(line) for line in (A03 / "INPUT_EVENTS.jsonl").read_text(
    encoding="utf-8").splitlines() if line]


def outcomes(rows) -> dict:
    results = {}
    for name, function in (("candidate", a03_candidate.reconstruct),
                           ("independent_auditor", a03_audit.independently_reconstruct)):
        try:
            result = function(rows)
            results[name] = {"accepted": True,
                             "reported_step": result["source_pair"]["step"]}
        except Exception as exc:
            results[name] = {"accepted": False, "error": type(exc).__name__}
    return results


def main() -> None:
    checks = []
    float_rows = copy.deepcopy(EVENTS)
    float_rows[1]["step"] = float(float_rows[0]["step"])
    checks.append({"case": "up_step_equal_float", "down_step": float_rows[0]["step"],
                   "up_step": float_rows[1]["step"], "outcomes": outcomes(float_rows)})

    boolean_rows = copy.deepcopy(EVENTS)
    boolean_rows[0]["step"], boolean_rows[1]["step"] = 1, True
    checks.append({"case": "down_one_up_true_equal_boolean", "down_step": 1,
                   "up_step": True, "outcomes": outcomes(boolean_rows)})
    print(json.dumps({"experiment": "A03 read-only in-memory cross-row step-type alias probe",
                      "retained_step": EVENTS[0]["step"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
