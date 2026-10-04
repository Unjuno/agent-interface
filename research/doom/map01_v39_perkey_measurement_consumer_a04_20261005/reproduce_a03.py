"""Read-only in-memory reproduction of A03's equal-type alias acceptance."""
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


def main() -> None:
    checks = []
    for index, field in ((0, "physical_down_interval"),
                         (1, "physical_up_interval")):
        rows = copy.deepcopy(EVENTS)
        interval = rows[index]["physical_key_measurement"]["bracket"][field]
        rows[index]["physical_key_measurement"]["bracket"][field] = [
            float(interval[0]), interval[1]]
        outcomes = {}
        for name, fn in (("candidate", a03_candidate.reconstruct),
                         ("independent_auditor", a03_audit.independently_reconstruct)):
            try:
                value = fn(rows)
                outcomes[name] = {"accepted": True,
                                  "preserved_interval": (value["down_state_interval_ns"]
                                                         if index == 0 else
                                                         value["up_state_interval_ns"])}
            except Exception as exc:  # recorded only as an acceptance/rejection outcome
                outcomes[name] = {"accepted": False, "error": type(exc).__name__}
        checks.append({"row": index, "field": field,
                       "mutation": "exact_float_alias_for_integer",
                       "outcomes": outcomes})
    result = {"experiment": "A03 read-only in-memory exact-type boundary probe",
              "baseline_candidate_schema": a03_candidate.reconstruct(EVENTS)["schema"],
              "checks": checks}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
