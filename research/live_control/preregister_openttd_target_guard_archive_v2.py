"""Correct image existence while preserving target/guard boxes and thresholds."""
import json

from preregister_openttd_target_guard_archive_v1 import HERE, case, sha


OUT = HERE / "results/openttd-target-guard-archive-02"


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    cases = [
        case("v6-first-segment", 6, "022.png", ["024.png", "025.png"], "met", 240, 288),
        case("v6-repeat-one", 6, "038.png", ["040.png", "041.png"], "target_not_reached", 240, 288),
        case("v6-repeat-two", 6, "045.png", ["048.png", "049.png"], "target_not_reached", 240, 288),
        case("v7-first-segment", 7, "025.png", ["027.png", "028.png"], "met", 240, 288),
        case("v7-second-segment-in-guard", 7, "029.png", ["031.png", "032.png"], "guard_changed", 240, 288),
        case("v8-first-segment", 8, "021.png", ["023.png", "024.png"], "met", 240, 288),
    ]
    sources = ["preregister_openttd_target_guard_archive_v1.py",
               "preregister_openttd_target_guard_archive_v2.py",
               "run_openttd_target_guard_archive_v2.py",
               "local_target_guard_postcondition_v1.py"]
    plan = {
        "status": "preregistered_before_reading_heldout_image_pixels",
        "correction": "v1 failed before heldout pixel read because v7/033.png did not exist; v2 uses the final two existing observations within each three-observation program and otherwise preserves endpoints",
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
