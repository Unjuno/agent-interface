"""Independent source decode and raw-event audit for the posthoc ammo timeline."""
import hashlib
import io
import json
from pathlib import Path

import av

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DATA = REPO / "research/doom/results/map01-astra-attempt-v1"
ANNOTATIONS = HERE / "AMMO_VIDEO_ANNOTATIONS.json"
RESULT = HERE / "AMMO_VIDEO_RESULT.json"
CROPS = HERE / "ammo-video-transition-crops"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def independently_decode(video_path, indices, roi):
    expected = set(indices)
    actual = {}
    with av.open(str(video_path)) as container:
        stream = container.streams.video[0]
        metadata = {"width": stream.width, "height": stream.height, "frames": stream.frames,
                    "fps": float(stream.average_rate)}
        for index, frame in enumerate(container.decode(stream)):
            if index in expected:
                buffer = io.BytesIO()
                frame.to_image().crop(tuple(roi)).save(buffer, format="PNG", optimize=False)
                actual[index] = {"video_seconds": float(frame.time), "crop": buffer.getvalue()}
    if set(actual) != expected:
        raise ValueError("AUDIT_VIDEO_FRAME_MISSING")
    return metadata, actual


def elapsed(ns, zero):
    return (ns - zero) / 1e9


def main():
    annotations = json.loads(ANNOTATIONS.read_text())
    report_path, events_path = DATA / "report.json", DATA / "events.jsonl"
    sidecar_path, video_path = DATA / "video.json", DATA / "map01-astra-live-01-2x.mp4"
    report = json.loads(report_path.read_text())
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    sidecar = json.loads(sidecar_path.read_text())
    video_hash = sha(video_path.read_bytes())
    input_hashes = {
        "video.mp4": video_hash,
        "video.json": sha(sidecar_path.read_bytes()),
        "events.jsonl": sha(events_path.read_bytes()),
        "report.json": sha(report_path.read_bytes()),
        "AMMO_VIDEO_ANNOTATIONS.json": sha(ANNOTATIONS.read_bytes()),
    }
    if video_hash != sidecar.get("sha256"):
        raise SystemExit("AUDIT_VIDEO_SIDECAR_HASH_MISMATCH")
    indices = {row["video_frame"] for row in annotations["endpoint_samples"]}
    for row in annotations["decrements"]:
        indices.update((row["before_frame"], row["after_frame"]))
    metadata, frames = independently_decode(video_path, indices, annotations["ammo_roi_xyxy"])
    if metadata != {"width": sidecar["width"], "height": sidecar["height"], "frames": sidecar["frames"], "fps": sidecar["fps"]}:
        raise SystemExit("AUDIT_VIDEO_METADATA_MISMATCH")
    result = json.loads(RESULT.read_text())
    mismatches = []
    if result.get("source_sha256") != input_hashes:
        mismatches.append("source-hashes")
    crop_manifest = result.get("crop_files", {})
    for index, decoded in frames.items():
        name = f"frame-{index:04d}-ammo.png"
        if sha(decoded["crop"]) != crop_manifest.get(name):
            mismatches.append(f"decoded-crop-hash:{index}")
        crop_path = CROPS / name
        if not crop_path.exists() or sha(crop_path.read_bytes()) != sha(decoded["crop"]):
            mismatches.append(f"retained-crop:{index}")

    ready = next(row["emit_ns"] for row in events if row.get("event") == "ready")
    observations = {row["sequence"]: row for row in events if row.get("event") == "observation"}
    expected_endpoints = []
    for label in annotations["endpoint_samples"]:
        seq, index = label["sequence"], label["video_frame"]
        event = observations[seq]
        mapped = frames[index]["video_seconds"] * annotations["source_playback_speed"]
        captured = elapsed(event["capture_ns"], ready)
        expected_endpoints.append({
            "sequence": seq, "capture_source_seconds": captured,
            "video_frame": index, "video_pts_seconds": frames[index]["video_seconds"],
            "mapped_source_seconds": mapped,
            "video_minus_capture_ms": (mapped-captured)*1e3,
            "ammo_manual": label["ammo_manual"],
            "ammo_roi_sha256": sha(frames[index]["crop"]),
        })
        if abs(mapped - captured) >= 0.1:
            mismatches.append(f"endpoint-time:{seq}")
    if result.get("endpoint_alignment") != expected_endpoints:
        mismatches.append("endpoint-alignment")

    acknowledgements = {}
    completions = {}
    for event in events:
        if event.get("id") != "cover-4":
            continue
        identity = event.get("step")
        if event.get("event") == "keys_held":
            acknowledgements[identity] = event
        elif event.get("event") == "step_completed":
            completions[identity] = event
    firing_windows = []
    for step, ack in sorted(acknowledgements.items()):
        if "space" in ack.get("keys", []):
            done = completions.get(step)
            if done is None:
                mismatches.append(f"missing-step-completion:{step}")
                continue
            firing_windows.append({
                "execution_id": "cover-4", "step": step, "keys": ack["keys"],
                "ack_source_seconds": elapsed(ack["emit_ns"], ready),
                "complete_source_seconds": elapsed(done["emit_ns"], ready),
            })
    if result.get("firing_steps") != firing_windows:
        mismatches.append("firing-step-rows")

    expected_transitions = []
    for row in annotations["decrements"]:
        before, after = row["before_frame"], row["after_frame"]
        start = frames[before]["video_seconds"] * annotations["source_playback_speed"]
        stop = frames[after]["video_seconds"] * annotations["source_playback_speed"]
        overlaps = []
        for window in firing_windows:
            shared = min(stop, window["complete_source_seconds"]) - max(start, window["ack_source_seconds"])
            if shared > 0:
                overlaps.append({"execution_id": window["execution_id"], "step": window["step"], "overlap_ms": shared*1e3})
        expected_transitions.append({
            "before_frame": before, "after_frame": after,
            "source_time_interval_seconds": [start, stop],
            "ammo_before_manual": row["ammo_before"], "ammo_after_manual": row["ammo_after"],
            "ammo_delta_manual": row["ammo_after"]-row["ammo_before"],
            "before_roi_sha256": sha(frames[before]["crop"]),
            "after_roi_sha256": sha(frames[after]["crop"]),
            "space_hold_lifecycle_overlaps": overlaps,
        })
    if result.get("transitions") != expected_transitions:
        mismatches.append("transition-joins")

    plan = report["decisions"][4]
    call_start, call_end = (elapsed(plan[key], ready) for key in ("controller_model_started_ns", "controller_model_ended_ns"))
    counts = {
        "inside": sum(x["source_time_interval_seconds"][0] >= call_start and x["source_time_interval_seconds"][1] <= call_end for x in expected_transitions),
        "straddling": sum(x["source_time_interval_seconds"][0] < call_start < x["source_time_interval_seconds"][1] for x in expected_transitions),
        "before": sum(x["source_time_interval_seconds"][1] <= call_start for x in expected_transitions),
    }
    if counts != {"inside": 9, "straddling": 1, "before": 1}:
        mismatches.append("model-window-decrement-counts")
    if not all(x["space_hold_lifecycle_overlaps"] for x in expected_transitions):
        mismatches.append("transition-without-cover-space-overlap")

    audit = {
        "schema": "map01-astra-ammo-video-audit-v1",
        "disposition": "PASS_AUDITED_POSTHOC_VIDEO_TEMPORAL_ASSOCIATION_HOLD_CAUSAL_ATTRIBUTION" if not mismatches else "FAIL_AMMO_VIDEO_AUDIT",
        "decoded_frame_count": len(frames),
        "endpoint_alignment_recomputed": expected_endpoints,
        "firing_steps_recomputed": firing_windows,
        "decrement_count_recomputed": len(expected_transitions),
        "model_window_counts_recomputed": counts,
        "transition_lifecycle_overlaps_recomputed": sum(bool(x["space_hold_lifecycle_overlaps"]) for x in expected_transitions),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "scope": "independent video-frame decode/hash and raw event timestamp joins; HUD numerals are manual transcriptions",
    }
    (HERE / "AMMO_VIDEO_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"disposition": audit["disposition"], "mismatches": mismatches, "decoding_frames": len(frames), "ammo_decrements": len(expected_transitions), "cover_firing_overlaps": audit["transition_lifecycle_overlaps_recomputed"], "model_window_counts": counts}, separators=(",", ":")))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
