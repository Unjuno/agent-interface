"""Calibrate path-derived boxes on frozen seed991004 OpenTTD frames."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from local_target_guard_postcondition_v1 import LocalTargetGuardPostcondition
from target_guard_from_paths_v1 import derive


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-guard-derived-archive-01"
ARCHIVE = HERE / "results/timing-envelope-openttd-l-11/fixed-astra/runtime"
FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
SECOND = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pixels(sequence):
    return np.asarray(Image.open(ARCHIVE / f"{sequence:03d}.png").convert("RGB"))


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    boxes = derive(FIRST, SECOND)
    spec = {
        "op": "local_target_guard_postcondition",
        "postcondition_id": "seed991004-first-road-segment",
        "source_sequence": 28,
        **{key: boxes[key] for key in ("target_boxes", "guard_boxes")},
        "pixel_delta_threshold": 24,
        "minimum_target_changed_pixels": 120,
        "maximum_guard_changed_pixels": 20,
        "required_samples": 2,
        "sample_interval_ms": 50,
        "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }
    source = pixels(28)
    condition = LocalTargetGuardPostcondition(spec, source, 28, "frozen-seed991004")

    def evaluate(sequences):
        return condition.evaluate([pixels(sequence) for sequence in sequences], sequences,
                                  ["frozen-seed991004"] * 2,
                                  [1_000_000_000, 1_050_000_000])

    outcomes = {
        "unchanged": evaluate([29, 30]),
        "first_segment_settled": evaluate([35, 36]),
        "later_segment_present": evaluate([61, 62]),
    }
    assert outcomes["unchanged"]["reason"] == "target_not_reached"
    assert outcomes["first_segment_settled"]["reason"] == "met"
    assert outcomes["later_segment_present"]["reason"] == "guard_changed"
    report = {
        "calibration_passed": True,
        "archive": "timing-envelope-openttd-l-11 fixed-astra seed991004",
        "archive_source_sequence": 28,
        "selected_sequence_pairs": {
            "unchanged": [29, 30], "first_segment_settled": [35, 36],
            "later_segment_present": [61, 62]},
        "first_path": FIRST,
        "continuation_path": SECOND,
        **boxes,
        "outcomes": outcomes,
        "sources": {
            "calibrate_openttd_target_guard_geometry_v1.py": sha(Path(__file__)),
            "target_guard_from_paths_v1.py": sha(HERE / "target_guard_from_paths_v1.py"),
            "local_target_guard_postcondition_v1.py": sha(HERE / "local_target_guard_postcondition_v1.py"),
            "source_028.png": sha(ARCHIVE / "028.png"),
            "unchanged_029.png": sha(ARCHIVE / "029.png"),
            "unchanged_030.png": sha(ARCHIVE / "030.png"),
            "target_035.png": sha(ARCHIVE / "035.png"),
            "target_036.png": sha(ARCHIVE / "036.png"),
            "guard_061.png": sha(ARCHIVE / "061.png"),
            "guard_062.png": sha(ARCHIVE / "062.png"),
        },
        "decision": "ADVANCE_PATH-DERIVED_BOXES_TO_ONE_PREREGISTERED_FRESH_SEED991004_PAIR",
        "scope": "posthoc selected frozen frames on one changed save; no fresh input, held-out visual geometry, model, latency, token or generalization claim",
    }
    (ROOT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
