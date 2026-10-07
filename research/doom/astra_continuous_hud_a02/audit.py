"""Independent standard-library audit for A02 threshold episode calculations."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
INPUT = REPO / "research/doom/astra_continuous_hud_a01/samples.csv"
A01_RESULT = REPO / "research/doom/astra_continuous_hud_a01/result.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independently_count_episodes(values: list[int], threshold: int) -> list[int]:
    result = []
    prior_above = values[0] > threshold
    for index in range(1, len(values)):
        current_above = values[index] > threshold
        if current_above and not prior_above:
            result.append(index)
        prior_above = current_above
    return result


def main() -> None:
    freeze = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    assert sha256(INPUT) == freeze["input_sha256"] == result["input"]["sha256"]
    assert sha256(A01_RESULT) == freeze["a01_result_sha256"]
    assert sha256(HERE / "analyze.py") == freeze["analysis_source_sha256"]
    assert sha256(HERE / "audit.py") == freeze["audit_source_sha256"]
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", freeze["base_commit"], "HEAD"],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).returncode == 0

    rows = list(csv.DictReader(INPUT.open(newline="", encoding="utf-8")))
    assert len(rows) == result["input"]["rows"] == 780
    assert [int(row["frame_index"]) for row in rows] == list(range(780))
    source_time = [float(row["source_control_elapsed_s"]) for row in rows]
    assert source_time[0] == 0.0 and source_time[-1] == 155.8
    assert all(abs((source_time[i] - source_time[i - 1]) - 0.2) < 0.0005
               for i in range(1, len(source_time)))
    diffs = [int(row["red_mask_xor_from_previous"]) for row in rows]
    params = freeze["parameters"]
    baseline_max = max(diffs[:params["baseline_last_frame_inclusive"] + 1])
    target_diff = diffs[params["selected_frame_index"]]
    assert baseline_max == params["baseline_max_required_pixels"] == 29
    assert target_diff == params["selected_frame_min_change_required_pixels"] == 471
    assert json.loads(A01_RESULT.read_text(encoding="utf-8"))[
        "pixel_change_probe"
    ]["selected_frame_mask_xor_from_previous_pixels"] == target_diff

    low, high = params["threshold_range_inclusive"]
    sweep = {
        threshold: independently_count_episodes(diffs, threshold)
        for threshold in range(low, high + 1)
    }
    detecting = {
        t: starts for t, starts in sweep.items()
        if params["selected_frame_index"] in starts
    }
    minimum = min(len(starts) for starts in detecting.values())
    best = sorted(t for t, starts in detecting.items() if len(starts) == minimum)
    assert minimum == result["measurements"][
        "minimum_episodes_while_detecting_selected_frame"
    ]
    assert best == result["measurements"]["thresholds_attaining_minimum"]

    for text_threshold, summary in result["measurements"][
        "selected_threshold_examples"
    ].items():
        threshold = int(text_threshold)
        assert len(sweep[threshold]) == summary["episodes"]
        assert (params["selected_frame_index"] in sweep[threshold]) == summary[
            "selected_frame_311_detected"
        ]

    audit = {
        "schema": "agent-interface-astra-change-alarm-threshold-a02-audit-v1",
        "status": "PASS_REPRODUCED_SCOPED",
        "checks": {
            "input_sha256_matches_freeze": True,
            "row_count_and_order": len(rows) == 780,
            "timeline_grid_0_to_155_8_s_at_0_2_s": True,
            "baseline_max_mask_xor_pixels": baseline_max,
            "frame311_mask_xor_pixels": target_diff,
            "threshold_candidates_recomputed": len(sweep),
            "thresholds_detecting_frame311": len(detecting),
            "minimum_episode_count": minimum,
            "thresholds_attaining_minimum": best,
            "example_threshold_summaries_match": True,
        },
        "scope": "Independent implementation reproduces arithmetic only; no semantic labeling of episodes, live-response claim, or formal allocation.",
        "result_sha256": sha256(HERE / "result.json"),
        "samples_csv_sha256": sha256(INPUT),
    }
    (HERE / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
