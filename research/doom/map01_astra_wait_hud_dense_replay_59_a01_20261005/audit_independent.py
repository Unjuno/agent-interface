#!/usr/bin/env python3
"""Independent red-pixel-change audit of the frozen HUD frame sequence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text())
INPUT = HERE / "input/health_roi.rgb"
CANDIDATE = Path(os.environ.get("RESULT_DIR", HERE / "results/a01")) / "candidate.raw.json"
OUT = Path(os.environ.get("RESULT_DIR", HERE / "results/a01")) / "independent_audit.json"
VISUAL = json.loads((HERE / "VISUAL_READOUT.json").read_text())


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_pixel_count(frame: bytes, baseline: bytes) -> int:
    """Count RGB pixels with a large change in at least one channel."""
    threshold = FREEZE["window"]["independent_audit_per_pixel_max_channel_abs_delta"]
    count = 0
    for i in range(0, len(frame), 3):
        if max(abs(frame[i + j] - baseline[i + j]) for j in range(3)) > threshold:
            count += 1
    return count


def main() -> None:
    for rel, expected in FREEZE["source_sha256"].items():
        assert sha((ROOT / rel).read_bytes()) == expected, "frozen source mismatch: " + rel
    video_meta = json.loads((ROOT / FREEZE["video"]["path"].replace("map01-astra-live-01-2x.mp4", "video.json")).read_text())
    assert video_meta["sha256"] == FREEZE["video"]["sha256"]
    raw = INPUT.read_bytes()
    count = FREEZE["window"]["frame_count"]
    frame_bytes = FREEZE["window"]["health_roi"]["width"] * FREEZE["window"]["health_roi"]["height"] * 3
    assert len(raw) == count * frame_bytes
    frames = [raw[i * frame_bytes : (i + 1) * frame_bytes] for i in range(count)]
    candidates = json.loads(CANDIDATE.read_text())
    assert candidates["input_sha256"] == sha(raw)
    assert candidates["frame_count"] == count
    threshold = FREEZE["window"]["independent_audit_threshold_changed_pixels"]
    baseline = frames[0]
    counts = [changed_pixel_count(frame, baseline) for frame in frames]
    changed = [i for i, n in enumerate(counts) if n >= threshold]
    first = changed[0] if changed else None
    assert first == 12, "thresholded independent view did not locate expected frame"
    assert all(x == 0 for x in counts[:first])
    assert counts[first] >= threshold
    candidate_first = candidates["first_changed_frame"]
    assert candidate_first["frame_index"] == first
    assert candidate_first["playback_seconds"] == 23.5
    assert candidates["last_baseline_frame"]["playback_seconds"] == 23.4
    samples = VISUAL["samples"]
    by_time = {x["playback_seconds"]: x for x in samples}
    assert by_time[23.4]["health"] == 100 and by_time[23.5]["health"] == 96
    assert by_time[28.1]["phase"] == "MODEL THINKING + LOCAL COVER" and by_time[28.1]["health"] == 94
    assert by_time[28.2]["phase"] == "LOCAL PLAN / FEEDBACK" and by_time[28.2]["health"] == 87
    for row in samples:
        p = HERE / row["image"]
        assert p.is_file() and p.stat().st_size > 1000
        assert sha(p.read_bytes()) == row["image_sha256"]
    report = json.loads((ROOT / "research/doom/results/map01-astra-attempt-v1/report.json").read_text())
    decision = report["decisions"][4]
    assert decision["model_ns"] == 11741060121
    assert decision["action"]["commands"] == [
        {"action": "backward", "extent": "short"},
        {"action": "turn_right", "extent": "short"},
    ]
    audit = {
        "schema": "map01-astra-decision4-dense-health-audit-v1",
        "run_id": FREEZE["run_id"],
        "status": "PASS_DESCRIPTIVE_VIDEO_FRAME_BOUNDARY_RECONSTRUCTION",
        "input_sha256": sha(raw),
        "candidate_raw_sha256": sha(CANDIDATE.read_bytes()),
        "audit_method": "independent per-pixel max-channel delta count against frame 0",
        "independent_pixel_threshold": threshold,
        "first_changed_frame_index": first,
        "first_changed_playback_seconds": 22.3 + first / 10,
        "first_changed_game_seconds": (22.3 + first / 10) * 2,
        "last_baseline_playback_seconds": 22.3 + (first - 1) / 10,
        "max_changed_pixels_before_transition": max(counts[:first]),
        "changed_pixels_at_transition": counts[first],
        "pending_to_feedback_health_delta_at_boundary": [94, 87],
        "model_wait_ns_from_retained_report": decision["model_ns"],
        "causal_damage_attribution": False,
        "live_runtime_claim": False,
    }
    OUT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: audit[k] for k in ("status", "first_changed_game_seconds", "last_baseline_playback_seconds", "changed_pixels_at_transition", "causal_damage_attribution")}, sort_keys=True))


if __name__ == "__main__":
    main()
