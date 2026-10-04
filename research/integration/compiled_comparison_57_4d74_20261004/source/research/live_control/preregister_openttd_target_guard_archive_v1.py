"""Freeze unseen archived OpenTTD checks for target/guard v1."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-guard-archive-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(run, image):
    return f"results/timing-envelope-openttd-l-{run:02d}/fixed-astra/runtime/{image}"


def case(name, run, source, samples, expected, target_y, guard_y):
    target_centers = [[705, target_y], [673, target_y + 16], [641, target_y + 32]]
    guard_centers = [[673, guard_y], [705, guard_y + 16]]
    paths = [relative(run, source)] + [relative(run, sample) for sample in samples]
    return {
        "name": name, "run": run, "source": paths[0], "samples": paths[1:],
        "expected": expected,
        "target_boxes": [[x - 6, y - 4, 12, 8] for x, y in target_centers],
        "guard_boxes": [[x - 6, y - 4, 12, 8] for x, y in guard_centers],
        "image_sha256": {path: sha(HERE / path) for path in paths},
    }


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    cases = [
        case("v6-first-segment", 6, "022.png", ["024.png", "025.png"], "met", 240, 288),
        case("v6-repeat-one", 6, "038.png", ["040.png", "041.png"], "target_not_reached", 240, 288),
        case("v6-repeat-two", 6, "045.png", ["048.png", "049.png"], "target_not_reached", 240, 288),
        case("v7-first-segment", 7, "025.png", ["028.png", "029.png"], "met", 240, 288),
        case("v7-second-segment-in-guard", 7, "029.png", ["032.png", "033.png"], "guard_changed", 240, 288),
        case("v8-first-segment", 8, "021.png", ["024.png", "025.png"], "met", 240, 288),
    ]
    sources = ["preregister_openttd_target_guard_archive_v1.py",
               "run_openttd_target_guard_archive_v1.py",
               "local_target_guard_postcondition_v1.py"]
    plan = {
        "status": "preregistered_before_reading_heldout_image_pixels",
        "development_evidence": {
            "runs": [9, 10, 11, 2], "pixel_delta_threshold": 24,
            "minimum_target_changed_pixels": 120, "maximum_guard_changed_pixels": 20,
            "observed_first_segment_target_ranges": [154, 179],
            "observed_first_segment_guard_ranges": [0, 1],
            "known_wrong_placement_target_changed": 36,
            "observed_later_guard_changed_ranges": [179, 186],
        },
        "heldout_cases": cases,
        "condition": {
            "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
            "maximum_guard_changed_pixels": 20, "required_samples": 2,
            "sample_interval_ms": 50, "timeout_ms": 500,
        },
        "primary_endpoint": "all three independently known first-segment effects are met; both completed-segment repeats are target_not_reached; the later second segment is guard_changed",
        "failure_policy": "retain first evaluation; do not change boxes or thresholds after reading heldout pixels",
        "truth_sources": {
            "v6_audit": sha(HERE / "audit_openttd_l_v6_posthoc.py"),
            "v7_audit": sha(HERE / "audit_openttd_l_v7.py"),
            "v8_audit": sha(HERE / "audit_openttd_l_v8.py"),
        },
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": "offline archived visual feasibility against engine-diagnosed effects; no live input, semantic scoring, latency or promotion claim",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
