#!/usr/bin/env python3
"""Independent structural audit of the frozen-rule reanalysis."""
import json
import sys
from pathlib import Path

EXPECTED_IDS = {f"high_confidence_falling_yield-{i:02d}" for i in range(6)}


def main(path):
    result = json.loads(Path(path).read_text())
    ids = {row["case_id"] for row in result["changed_velocity_rows"]}
    errors = []
    if result["classification"] != "FROZEN_RULE_REANALYSIS_NOT_NEW_OBSERVATIONS":
        errors.append("classification")
    if result["rows"] != 84:
        errors.append("row_count")
    if ids != EXPECTED_IDS:
        errors.append(f"changed_ids:{sorted(ids)}")
    if result["metrics"].get("CURRENT_ONLY") != {"typed_accuracy": 66, "false_action": 12}:
        errors.append("current_metrics")
    if result["metrics"].get("LEVEL_PLUS_VELOCITY") != {"typed_accuracy": 72, "false_action": 12}:
        errors.append("velocity_metrics")
    print(json.dumps({"checks": 5, "errors": errors}, sort_keys=True))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
