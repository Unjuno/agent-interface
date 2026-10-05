"""Freeze a settle-aligned retry without changing target/guard boxes or thresholds."""
import json

from preregister_openttd_target_guard_archive_v1 import HERE, case, sha


OUT = HERE / "results/openttd-target-guard-archive-03"


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    cases = [
        case("v6-first-segment", 6, "022.png", ["024.png", "025.png"], "met", 240, 288),
        case("v6-repeat-one", 6, "038.png", ["040.png", "041.png"], "target_not_reached", 240, 288),
        case("v6-repeat-two", 6, "045.png", ["048.png", "049.png"], "target_not_reached", 240, 288),
        case("v7-first-segment", 7, "025.png", ["028.png", "029.png"], "met", 240, 288),
        case("v7-second-segment-in-guard", 7, "029.png", ["031.png", "032.png"], "guard_changed", 240, 288),
        case("v8-first-segment", 8, "021.png", ["024.png", "025.png"], "met", 240, 288),
    ]
    sources = ["preregister_openttd_target_guard_archive_v1.py",
               "preregister_openttd_target_guard_archive_v3.py",
               "run_openttd_target_guard_archive_v3.py",
               "local_target_guard_postcondition_v1.py", "session_v25.py"]
    previous = json.loads((HERE / "results/openttd-target-guard-archive-02/preregistration.json").read_text())
    plan = {
        "status": "preregistered_before_reading_corrected_sample_pixels",
        "correction": "v2 retained two false stops because an in-program observation before the persistent effect was counted as a required sample; v3 models the newly required bounded settle using the final effect observation plus the next passive observation",
        "unchanged_from_v2": {
            "development_evidence": previous["development_evidence"],
            "condition": previous["condition"],
            "target_and_guard_boxes": True,
            "expected_reasons": True,
        },
        "cases": cases,
        "primary_endpoint": previous["primary_endpoint"],
        "failure_policy": "retain first corrected evaluation; no threshold or box changes",
        "truth_sources": previous["truth_sources"],
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": "offline settle-aligned archived visual feasibility against engine-diagnosed effects; no live input, semantic scoring, latency or promotion claim",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
