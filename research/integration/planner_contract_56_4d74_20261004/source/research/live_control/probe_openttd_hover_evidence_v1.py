"""Replay archived tooltips and reject malformed hover associations."""
import json
import shutil
import tempfile
from pathlib import Path

from hover_target_contract_v1 import runtime_reference
from openttd_hover_evidence_v1 import CANDIDATES, ORDER, classify, verify


HERE = Path(__file__).resolve().parent
SAMPLES = {
    "subsidies": HERE / "results/timing-envelope-openttd-matched-02/fixed-luna/runtime/020.png",
    "trains": HERE / "results/timing-envelope-openttd-matched-02/fixed-luna/runtime/004.png",
    "roads": HERE / "results/timing-envelope-openttd-matched-05/fixed-astra/runtime/012.png",
}


for name, path in SAMPLES.items():
    result = classify(path)
    assert result["candidate_id"] == name
    assert result["point"] == CANDIDATES[name]["point"]

with tempfile.TemporaryDirectory() as raw:
    runtime = Path(raw)
    binding = {"focus": 1, "surface": 2, "geometry": [3, 4, 1280, 800]}
    steps = []
    records = []
    for index, name in enumerate(ORDER):
        image = runtime / f"{name}.png"
        shutil.copy2(SAMPLES[name], image)
        x, y = CANDIDATES[name]["point"]
        steps += [{"op": "pointer_move", "x": x, "y": y},
                  {"op": "dwell_observe", "delay_ms": 800},
                  {"op": "observe"}]
        records.append({"event": "pointer_admission", "step": index * 3,
                        "operation": "move", "payload": {"x": x, "y": y}})
        for offset in (1, 2):
            records.append({"event": "observation", "step": index * 3 + offset,
                            "sequence": index * 2 + offset,
                            "image": str(image), "focus_samples_match": True,
                            "pointer_binding": binding})
    ready = verify(records, steps, runtime)
    assert ready["status"] == "READY"
    assert [row["candidate_id"] for row in ready["evidence"]] == ORDER
    association_refused = 0
    for changed_records, changed_steps, changed_order in [
            (records, steps, ["trains", "subsidies", "roads"]),
            (records[:-1], steps, ORDER),
            ([{**row, "pointer_binding": {**binding, "focus": 9}}
              if row.get("event") == "observation" and row.get("step") == 5 else row
              for row in records], steps, ORDER),
            (records, steps[:-1], ORDER)]:
        try:
            verify(changed_records, changed_steps, runtime, changed_order)
        except ValueError:
            association_refused += 1
        else:
            raise AssertionError("malformed hover association accepted")

valid = {
    "op": "target_reference", "candidate_id": "roads",
    "point_space": "source_observation_pixels",
    "point": {"x": 820, "y": 51},
    "motion_model": "surface_origin_translation",
}
assert runtime_reference(valid) == {
    "candidate_id": "roads", "point": [820, 51],
    "coordinate_frame": "window_content",
    "point_space": "source_observation_pixels",
    "motion_model": "surface_origin_translation",
}
invalid = [
    {**valid, "candidate_id": "trains"},
    {**valid, "point": {"x": 819, "y": 51}},
    {**valid, "point_space": "presentation_pixels"},
    {**valid, "motion_model": "unknown"},
    {key: value for key, value in valid.items() if key != "candidate_id"},
    {**valid, "extra": True},
]
refused = 0
for value in invalid:
    try:
        runtime_reference(value)
    except ValueError:
        refused += 1
    else:
        raise AssertionError(value)
assert refused == len(invalid)
print(json.dumps({"archived_templates_classified": len(SAMPLES),
                  "invalid_contracts_refused": refused,
                  "valid_hover_bundle_ready": True,
                  "invalid_hover_bundles_refused": association_refused,
                  "candidate_points": {name: spec["point"]
                                       for name, spec in CANDIDATES.items()}}))
