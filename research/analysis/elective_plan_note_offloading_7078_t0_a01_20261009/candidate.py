#!/usr/bin/env python3
"""Frozen-input elective note selector; authored method fixture only."""
import json
import sys
from pathlib import Path


def losses(case):
    q0, q1, loss = case["q0"], case["q1"], case["safe_rediscovery_loss"]
    d, cost = case["delivery_probability"], case["forecast_write_read_cost"]
    return (1 - q0) * loss, cost + d * (1 - q1) * loss + (1 - d) * (1 - q0) * loss


def run(data):
    rows = []
    for case in data["cases"]:
        no_note, note = losses(case)
        eligible = (case["delivered"] and case["source"] == case["note_source"]
                    and case["generation"] == 9 and case["q0_kind"] == "future_unaided_forecast")
        choice = "NOTE" if eligible and note < no_note else "NO_NOTE"
        rows.append({"id": case["id"], "choice": choice, "no_note_loss": no_note, "note_loss": note,
                     "mandatory_ids": [r["id"] for r in data["mandatory"]]})
    return {"schema": "7078-t0-a01-output-v1", "rows": rows,
            "calibration_ids": data["calibration_ids"], "held_out_ids": data["held_out_ids"]}


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    dst.write_text(json.dumps(run(json.loads(src.read_text())), sort_keys=True, indent=2) + "\n")
