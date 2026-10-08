#!/usr/bin/env python3
"""Pre-freeze corruption tests for the independent raw-only auditor."""
import copy
import json
import sys
from pathlib import Path

from auditor import verify


def main(input_path, raw_path, report_path):
    config = json.loads(Path(input_path).read_text())
    raw = json.loads(Path(raw_path).read_text())
    tests = {}

    x = copy.deepcopy(raw)
    x["cases"][0]["rows"].pop()
    tests["dropped_attempt_row"] = bool(verify(config, x))

    x = copy.deepcopy(raw)
    x["cases"][0]["rows"][0]["state"] = 1-x["cases"][0]["rows"][0]["state"]
    tests["changed_truth_state"] = bool(verify(config, x))

    x = copy.deepcopy(raw)
    x["cases"][0]["rows"][0]["authority"] = "EXECUTE"
    tests["authority_escalation"] = bool(verify(config, x))

    x = copy.deepcopy(raw)
    row = next(r for c in x["cases"] for r in c["rows"] if r["delivered"] == 0)
    row["used_signal"] = True
    tests["false_consumption_receipt"] = bool(verify(config, x))

    x = copy.deepcopy(raw)
    stale = next(c for c in x["cases"] if c["case_id"] == "stale_signal")
    stale["rows"][0]["observed_signal"] = stale["rows"][0]["latent_signal"]
    tests["stale_signal_promotion"] = bool(verify(config, x))

    x = copy.deepcopy(raw)
    x["pair_comparisons"]["reference"]["split_A_lt_B"] = False
    tests["forged_pair_ranking"] = bool(verify(config, x))

    result = {"status": "PASS_CONSTRUCTION" if all(tests.values()) else "FAIL_CONSTRUCTION",
              "mutations_detected": sum(tests.values()), "mutations_total": len(tests),
              "tests": tests}
    Path(report_path).write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if all(tests.values()) else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: construction_check.py INPUT_JSON CONSTRUCTION_RAW REPORT_JSON")
    raise SystemExit(main(*sys.argv[1:]))
