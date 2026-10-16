"""Replay generic hover receipts and evidence-bound target controls."""
import copy
import json
from pathlib import Path

from evidence_target_contract_v1 import validate as validate_target
from openttd_hover_receipt_v1 import verify


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results-local/openttd-toolbar-probe-dev-04/runtime"
POINTS = [[456, 51], [480, 51], [504, 51]]


events = [json.loads(line) for line in (ROOT / "events.jsonl").read_text().splitlines()]
terminal = next(row for row in events if row.get("event") == "terminal"
                and row.get("steps_completed") == 9)
records = [row for row in events if row.get("id") == terminal["id"]]
command = next(row["command"] for row in events if row.get("event") == "command"
               and row.get("command", {}).get("id") == terminal["id"])
readiness = verify(records, command["steps"], POINTS, ROOT)
assert readiness["status"] == "READY" and len(readiness["receipts"]) == 3
selection = {"op": "target_reference", "receipt_index": 2,
             "point_space": "source_observation_pixels",
             "point": {"x": 480, "y": 51},
             "motion_model": "surface_origin_translation",
             "evidence_kind": "persistent_hover_tooltip"}
assert validate_target(selection, readiness)["point"] == [480, 51]

invalid_receipts = []
wrong_steps = copy.deepcopy(command["steps"])
wrong_steps[0]["x"] += 1
invalid_receipts.append((records, wrong_steps))
missing = [row for row in records
           if not (row.get("event") == "observation" and row.get("step") == 2)]
invalid_receipts.append((missing, command["steps"]))
changed_binding = copy.deepcopy(records)
next(row for row in changed_binding if row.get("event") == "observation"
     and row.get("step") == 2)["pointer_binding"]["focus"] = 9
invalid_receipts.append((changed_binding, command["steps"]))
receipt_refusals = 0
for candidate_records, candidate_steps in invalid_receipts:
    try:
        verify(candidate_records, candidate_steps, POINTS, ROOT)
    except ValueError:
        receipt_refusals += 1
    else:
        raise AssertionError("invalid hover receipt bundle accepted")

invalid_targets = [None, {**selection, "extra": 1},
                   {**selection, "receipt_index": 4},
                   {**selection, "receipt_index": 1},
                   {**selection, "evidence_kind": "model_guess"}]
target_refusals = 0
for candidate in invalid_targets:
    try:
        validate_target(candidate, readiness)
    except ValueError:
        target_refusals += 1
    else:
        raise AssertionError("invalid evidence target accepted")

print(json.dumps({"generic_hover_receipts": len(readiness["receipts"]),
                  "invalid_receipt_bundles_refused": receipt_refusals,
                  "evidence_bound_target": True,
                  "invalid_targets_refused": target_refusals,
                  "tooltip_digests": [row["tooltip"]["pixels_sha256"]
                                      for row in readiness["receipts"]]}))
