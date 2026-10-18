"""Exploratory posthoc sweep of the retained Astra A01 ROI-change alarm."""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
INPUT = REPO / "research/doom/astra_continuous_hud_a01/samples.csv"
A01_RESULT = REPO / "research/doom/astra_continuous_hud_a01/result.json"
EXPECTED_INPUT_SHA256 = "0b585a3671a10ba2a3e4f634b32cddc7f3fb83aa85013eb75faff8a128cd7e97"
EXPECTED_A01_HEAD = "b23585118af985096974cb8a9d19518a3d0ad914"
SELECTED_FRAME = 311
BASELINE_LAST_FRAME = 220
LOW_THRESHOLD = 30
HIGH_THRESHOLD = 470


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_starts(values: list[int], threshold: int) -> list[int]:
    starts = []
    previous_above = False
    for index, value in enumerate(values):
        above = value > threshold
        if above and not previous_above:
            starts.append(index)
        previous_above = above
    return starts


def main() -> None:
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_A01_HEAD, "HEAD"],
        cwd=REPO, capture_output=True,
    )
    assert ancestry.returncode == 0
    input_sha = sha256(INPUT)
    assert input_sha == EXPECTED_INPUT_SHA256, input_sha
    rows = list(csv.DictReader(INPUT.open(newline="", encoding="utf-8")))
    assert len(rows) == 780
    assert [int(row["frame_index"]) for row in rows] == list(range(780))
    diffs = [int(row["red_mask_xor_from_previous"]) for row in rows]
    baseline_max = max(diffs[:BASELINE_LAST_FRAME + 1])
    target_diff = diffs[SELECTED_FRAME]
    assert baseline_max == 29
    assert target_diff == 471

    sweep = []
    for threshold in range(LOW_THRESHOLD, HIGH_THRESHOLD + 1):
        starts = event_starts(diffs, threshold)
        sweep.append({
            "threshold_pixels_exclusive": threshold,
            "event_episode_count": len(starts),
            "event_start_frame_indices": starts,
            "selected_frame_311_detected": SELECTED_FRAME in starts,
        })
    eligible = [row for row in sweep if row["selected_frame_311_detected"]]
    minimum = min(row["event_episode_count"] for row in eligible)
    best_thresholds = [
        row["threshold_pixels_exclusive"] for row in eligible
        if row["event_episode_count"] == minimum
    ]
    summaries = {}
    for threshold in (30, 60, 100, 200, 300, 400, 466, 470):
        item = next(row for row in sweep
                    if row["threshold_pixels_exclusive"] == threshold)
        summaries[str(threshold)] = {
            "episodes": item["event_episode_count"],
            "selected_frame_311_detected": item["selected_frame_311_detected"],
        }
    a01 = json.loads(A01_RESULT.read_text(encoding="utf-8"))
    assert a01["pixel_change_probe"][
        "selected_frame_mask_xor_from_previous_pixels"
    ] == target_diff

    result = {
        "schema": "agent-interface-astra-change-alarm-threshold-a02-v1",
        "status": "EXPLORATORY_SCOPED",
        "question": "Can a fixed scalar threshold on A01's red-mask XOR signal uniquely isolate the manually selected frame-311 change within this retained run?",
        "H_T_D_C_U": {
            "H": "Among scalar thresholds above the stable pre-decision baseline that still detect frame 311, no threshold yields a single event episode in this 780-frame trace.",
            "T": "Recompute threshold-crossing episodes from all 780 retained A01 CSV rows for every integer threshold 30 through 470 pixels; an episode begins above threshold after the preceding frame is at or below threshold.",
            "D": "The scoped calculation reproduces baseline maximum 29 pixels, frame-311 change 471 pixels, and a minimum episode count greater than one among thresholds that detect frame 311.",
            "C": "Other episodes may be real health changes or other meaningful HUD updates, not nuisance or false alarms. A static threshold could still be useful as a broad observation trigger if its cost and response policy are acceptable.",
            "U": "One rendered attempt, one fixed ROI and color threshold, 5 video frames/s at 2x playback (0.2 source seconds between rows), no semantic labels for the other episodes, no live detector or controller response.",
        },
        "input": {
            "path": "research/doom/astra_continuous_hud_a01/samples.csv",
            "sha256": input_sha,
            "bytes": INPUT.stat().st_size,
            "rows": len(rows),
            "frame_range_inclusive": [0, 779],
            "source_elapsed_range_s": [
                float(rows[0]["source_control_elapsed_s"]),
                float(rows[-1]["source_control_elapsed_s"]),
            ],
            "source_step_s": round(
                float(rows[1]["source_control_elapsed_s"])
                - float(rows[0]["source_control_elapsed_s"]), 6
            ),
        },
        "measurements": {
            "stable_baseline_through_frame_220_max_mask_xor_pixels": baseline_max,
            "selected_frame_index": SELECTED_FRAME,
            "selected_frame_mask_xor_pixels": target_diff,
            "candidate_thresholds_inclusive_pixels": [LOW_THRESHOLD, HIGH_THRESHOLD],
            "candidate_threshold_count": len(sweep),
            "minimum_episodes_while_detecting_selected_frame": minimum,
            "thresholds_attaining_minimum": best_thresholds,
            "selected_threshold_examples": summaries,
        },
        "interpretation": "The generic ROI-change threshold is not a unique event selector in this trace. This does not establish a false-alarm rate, health-classification performance, or that the other events should be ignored. It is insufficient by itself to authorize policy interruption or escalation.",
        "decision": "Do not treat the A01 scalar ROI-change alarm alone as a live policy-interrupt trigger. A fresh live test needs a semantically grounded state delta or an explicitly bounded observation-only response, followed by a tested policy-validity decision.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "runner": "local posthoc CPU analysis; no game, model, GUI, OS input, or container launched",
        },
    }
    assert minimum > 1
    (HERE / "result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )

    freeze = {
        "schema": "agent-interface-astra-change-alarm-threshold-a02-freeze-v1",
        "base_commit": EXPECTED_A01_HEAD,
        "input_sha256": input_sha,
        "a01_result_sha256": sha256(A01_RESULT),
        "analysis_source_sha256": sha256(Path(__file__)),
        "audit_source_sha256": sha256(HERE / "audit.py"),
        "parameters": {
            "baseline_last_frame_inclusive": BASELINE_LAST_FRAME,
            "baseline_max_required_pixels": 29,
            "selected_frame_index": SELECTED_FRAME,
            "selected_frame_min_change_required_pixels": 471,
            "threshold_range_inclusive": [LOW_THRESHOLD, HIGH_THRESHOLD],
            "crossing_operator": "strictly greater than threshold",
            "episode_rule": "rising edge: current diff > threshold and previous diff <= threshold; frame 0 uses its recorded zero predecessor",
        },
        "provenance_note": "Exploratory PowerShell calculations preceded this package. This freeze pins the exact source and reproduces the observed measurements; it is not prospective preregistration for a formal allocation.",
        "scope": "Read-only posthoc reconstruction from A01 retained measurements; one attempt; no live allocation or intervention.",
    }
    (HERE / "freeze.json").write_text(
        json.dumps(freeze, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"],
        "rows": len(rows),
        "input_sha256": input_sha,
        "baseline_max": baseline_max,
        "frame311_diff": target_diff,
        "minimum_episodes": minimum,
        "thresholds_at_minimum": best_thresholds,
    }, indent=2))


if __name__ == "__main__":
    main()
