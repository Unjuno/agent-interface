"""Evaluate corrected preregistered OpenTTD target/guard archives."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from local_target_guard_postcondition_v1 import LocalTargetGuardPostcondition


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-guard-archive-02"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels(path):
    return np.asarray(Image.open(path).convert("RGB"))


def main():
    plan = json.loads((OUT / "preregistration.json").read_text())
    assert plan["status"] == "preregistered_before_reading_heldout_image_pixels"
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    rows = []
    for index, case in enumerate(plan["heldout_cases"]):
        for path, expected in case["image_sha256"].items():
            assert sha(HERE / path) == expected, path
        condition = {
            "op": "local_target_guard_postcondition",
            "postcondition_id": case["name"], "source_sequence": 1,
            "target_boxes": case["target_boxes"], "guard_boxes": case["guard_boxes"],
            **plan["condition"], "on_unmet": "needs_decision",
        }
        evaluator = LocalTargetGuardPostcondition(
            condition, pixels(HERE / case["source"]), 1, "archived-openttd")
        outcome = evaluator.evaluate(
            [pixels(HERE / path) for path in case["samples"]], [2, 3],
            ["archived-openttd", "archived-openttd"],
            [1_000_000_000 + index * 1_000_000_000,
             1_050_000_000 + index * 1_000_000_000])
        rows.append({"name": case["name"], "expected": case["expected"],
                     "outcome": outcome})
    passed = all(row["outcome"]["reason"] == row["expected"] for row in rows)
    report = {
        "passed": passed, "cases": rows,
        "decision": ("ADVANCE_TARGET_GUARD_TO_FRESH_X11_INTEGRATION" if passed else
                     "REJECT_OR_REVISE_TARGET_GUARD;_PRESERVE_HELDOUT_RESULT"),
        "scope": plan["scope"],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
