"""Audit the frozen-frame calibration for path-derived OpenTTD target/guard boxes."""
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pixels(sequence):
    return np.asarray(Image.open(ARCHIVE / f"{sequence:03d}.png").convert("RGB"))


def main():
    report = json.loads((ROOT / "report.json").read_text())
    source_paths = {
        "calibrate_openttd_target_guard_geometry_v1.py": HERE / "calibrate_openttd_target_guard_geometry_v1.py",
        "target_guard_from_paths_v1.py": HERE / "target_guard_from_paths_v1.py",
        "local_target_guard_postcondition_v1.py": HERE / "local_target_guard_postcondition_v1.py",
        "source_028.png": ARCHIVE / "028.png",
        "unchanged_029.png": ARCHIVE / "029.png",
        "unchanged_030.png": ARCHIVE / "030.png",
        "target_035.png": ARCHIVE / "035.png",
        "target_036.png": ARCHIVE / "036.png",
        "guard_061.png": ARCHIVE / "061.png",
        "guard_062.png": ARCHIVE / "062.png",
    }
    source_hashes_match = all(
        report["sources"][name] == sha(path) for name, path in source_paths.items()
    )
    boxes = derive(report["first_path"], report["continuation_path"])
    boxes_match = all(report[key] == boxes[key] for key in (
        "target_boxes", "guard_boxes", "derivation"))
    spec = {
        "op": "local_target_guard_postcondition",
        "postcondition_id": "seed991004-first-road-segment",
        "source_sequence": 28,
        "target_boxes": boxes["target_boxes"],
        "guard_boxes": boxes["guard_boxes"],
        "pixel_delta_threshold": 24,
        "minimum_target_changed_pixels": 120,
        "maximum_guard_changed_pixels": 20,
        "required_samples": 2,
        "sample_interval_ms": 50,
        "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }
    condition = LocalTargetGuardPostcondition(spec, pixels(28), 28, "frozen-seed991004")
    pairs = report["selected_sequence_pairs"]
    recomputed = {}
    for name, sequences in pairs.items():
        recomputed[name] = condition.evaluate(
            [pixels(sequence) for sequence in sequences], sequences,
            ["frozen-seed991004"] * 2, [1_000_000_000, 1_050_000_000])
    outcomes_match = recomputed == report["outcomes"]
    reasons = {name: outcome["reason"] for name, outcome in recomputed.items()}
    expected_reasons = {
        "unchanged": "target_not_reached",
        "first_segment_settled": "met",
        "later_segment_present": "guard_changed",
    }
    audit = {
        "audit_passed": source_hashes_match and boxes_match and outcomes_match
        and reasons == expected_reasons,
        "source_hashes_match": source_hashes_match,
        "derived_boxes_match": boxes_match,
        "outcomes_match": outcomes_match,
        "recomputed_reasons": reasons,
        "expected_reasons": expected_reasons,
    }
    assert audit["audit_passed"]
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
