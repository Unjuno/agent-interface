"""Posthoc time-map video-derived ammo HUD transitions to retained raw events."""
import hashlib
import io
import json
from pathlib import Path

import av

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DATA = REPO / "research/doom/results/map01-astra-attempt-v1"
ANNOTATIONS = HERE / "AMMO_VIDEO_ANNOTATIONS.json"
OUT = HERE / "AMMO_VIDEO_RESULT.json"
CROPS = HERE / "ammo-video-transition-crops"


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def decode_crops(video_path, frame_indices, roi):
    wanted = set(frame_indices)
    found = {}
    container = av.open(str(video_path))
    stream = container.streams.video[0]
    for index, frame in enumerate(container.decode(stream)):
        if index not in wanted:
            continue
        image = frame.to_image().crop(tuple(roi))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=False)
        found[index] = {
            "pts": frame.pts,
            "video_seconds": float(frame.time),
            "crop_png": buffer.getvalue(),
        }
    if set(found) != wanted:
        raise ValueError("VIDEO_FRAME_MISSING")
    return stream, found


def _relative_ns(ns, ready_ns):
    return (ns - ready_ns) / 1e9


def build(report, events, video_sidecar, annotations, frame_data, video_sha256):
    ready = next(row["emit_ns"] for row in events if row.get("event") == "ready")
    speed = annotations["source_playback_speed"]
    fps = annotations["source_fps"]
    if speed != video_sidecar.get("source_playback_speed") or fps != video_sidecar.get("fps"):
        raise ValueError("VIDEO_TIMING_METADATA_MISMATCH")

    ammo_labels = {117: 50, 148: 48, 211: 37}
    observations = {
        row["sequence"]: row for row in events
        if row.get("event") == "observation" and row.get("sequence") in ammo_labels
    }
    if set(observations) != set(ammo_labels):
        raise ValueError("AMMO_ENDPOINT_OBSERVATION_MISSING")
    endpoints = []
    for annotation in annotations["endpoint_samples"]:
        seq, frame_index = annotation["sequence"], annotation["video_frame"]
        sample = observations[seq]
        source_s = _relative_ns(sample["capture_ns"], ready)
        video_source_s = frame_data[frame_index]["video_seconds"] * speed
        if abs(source_s - video_source_s) >= 0.1:
            raise ValueError("VIDEO_EVENT_ALIGNMENT_OUTSIDE_100MS")
        if annotation["ammo_manual"] != ammo_labels[seq]:
            raise ValueError("VIDEO_ENDPOINT_HUD_LABEL_MISMATCH")
        endpoints.append({
            "sequence": seq,
            "capture_source_seconds": source_s,
            "video_frame": frame_index,
            "video_pts_seconds": frame_data[frame_index]["video_seconds"],
            "mapped_source_seconds": video_source_s,
            "video_minus_capture_ms": (video_source_s - source_s) * 1e3,
            "ammo_manual": annotation["ammo_manual"],
            "ammo_roi_sha256": digest_bytes(frame_data[frame_index]["crop_png"]),
        })

    ready_ns = ready
    decision4 = report["decisions"][4]
    plan4_start = _relative_ns(decision4["controller_model_started_ns"], ready_ns)
    plan4_end = _relative_ns(decision4["controller_model_ended_ns"], ready_ns)
    step_ack = {}
    step_done = {}
    for event in events:
        if event.get("event") == "keys_held" and event.get("id") == "cover-4":
            identity = event.get("step")
            if identity in step_ack:
                raise ValueError("DUPLICATE_COVER_STEP_ACK")
            step_ack[identity] = event
        elif event.get("event") == "step_completed" and event.get("id") == "cover-4":
            identity = event.get("step")
            if identity in step_done:
                raise ValueError("DUPLICATE_COVER_STEP_COMPLETION")
            step_done[identity] = event
    firing_steps = []
    for step, ack in sorted(step_ack.items()):
        if "space" not in ack.get("keys", []):
            continue
        done = step_done.get(step)
        if done is None:
            raise ValueError("FIRING_STEP_COMPLETION_MISSING")
        firing_steps.append({
            "execution_id": "cover-4",
            "step": step,
            "keys": ack["keys"],
            "ack_source_seconds": _relative_ns(ack["emit_ns"], ready_ns),
            "complete_source_seconds": _relative_ns(done["emit_ns"], ready_ns),
        })

    transitions = []
    for row in annotations["decrements"]:
        before, after = row["before_frame"], row["after_frame"]
        start_s = frame_data[before]["video_seconds"] * speed
        stop_s = frame_data[after]["video_seconds"] * speed
        overlaps = []
        for step in firing_steps:
            overlap = min(stop_s, step["complete_source_seconds"]) - max(start_s, step["ack_source_seconds"])
            if overlap > 0:
                overlaps.append({"execution_id": step["execution_id"], "step": step["step"], "overlap_ms": overlap * 1e3})
        transitions.append({
            "before_frame": before,
            "after_frame": after,
            "source_time_interval_seconds": [start_s, stop_s],
            "ammo_before_manual": row["ammo_before"],
            "ammo_after_manual": row["ammo_after"],
            "ammo_delta_manual": row["ammo_after"] - row["ammo_before"],
            "before_roi_sha256": digest_bytes(frame_data[before]["crop_png"]),
            "after_roi_sha256": digest_bytes(frame_data[after]["crop_png"]),
            "space_hold_lifecycle_overlaps": overlaps,
        })
    if len(firing_steps) != 5 or len(transitions) != 11:
        raise ValueError("UNEXPECTED_COVER_AMMO_ROW_COUNTS")
    if any(row["ammo_delta_manual"] != -1 or not row["space_hold_lifecycle_overlaps"] for row in transitions):
        raise ValueError("AMMO_TRANSITION_NOT_JOINED_TO_FIRING_STEP")

    plan3_terminal = next(row for row in events if row.get("event") == "terminal" and row.get("id") == "plan-3-primary-0-1")
    release3 = plan3_terminal["release"]
    release3_s = _relative_ns(release3["verified_ns"], ready_ns)
    return {
        "schema": "map01-astra-ammo-video-timeline-v1",
        "disposition": "PASS_POSTHOC_VIDEO_TEMPORAL_ASSOCIATION_HOLD_CAUSAL_ATTRIBUTION",
        "source_sha256": {
            "video.mp4": video_sha256,
            "video.json": hashlib.sha256((DATA / "video.json").read_bytes()).hexdigest(),
            "events.jsonl": hashlib.sha256((DATA / "events.jsonl").read_bytes()).hexdigest(),
            "report.json": hashlib.sha256((DATA / "report.json").read_bytes()).hexdigest(),
            "AMMO_VIDEO_ANNOTATIONS.json": hashlib.sha256(ANNOTATIONS.read_bytes()).hexdigest(),
        },
        "video_decode": {
            "decoder": "PyAV",
            "pyav_version": av.__version__,
            "width": video_sidecar["width"],
            "height": video_sidecar["height"],
            "fps": fps,
            "frame_count": video_sidecar["frames"],
            "source_playback_speed": speed,
            "source_time_mapping": "monotonic source seconds = decoded video PTS seconds * source_playback_speed, relative to ready",
            "ammo_roi_xyxy": annotations["ammo_roi_xyxy"],
        },
        "endpoint_alignment": endpoints,
        "plan4_model_window_source_seconds": [plan4_start, plan4_end],
        "plan3_owner_release_verified_source_seconds": release3_s,
        "ammo_decrement_count": len(transitions),
        "ammo_decrements_during_plan4_model_window": sum(
            row["source_time_interval_seconds"][0] >= plan4_start
            and row["source_time_interval_seconds"][1] <= plan4_end for row in transitions
        ),
        "ammo_decrements_straddling_plan4_model_start": sum(
            row["source_time_interval_seconds"][0] < plan4_start
            < row["source_time_interval_seconds"][1] for row in transitions
        ),
        "ammo_decrements_before_plan4_model_start": sum(
            row["source_time_interval_seconds"][1] <= plan4_start for row in transitions
        ),
        "firing_steps": firing_steps,
        "transitions": transitions,
        "all_transition_intervals_overlap_cover4_space_hold_lifecycle": all(
            row["space_hold_lifecycle_overlaps"] for row in transitions
        ),
        "interpretation": (
            "The video-bounded 48-to-37 HUD decrease appears as 11 one-round transitions "
            "between source times 44.2 and 53.8 seconds. All 11 transition brackets overlap "
            "a cover-4 keys_held-to-step_completed lifecycle whose key set includes space. "
            "One decrement precedes plan 4 model start, one bracket straddles its start, "
            "and nine brackets lie wholly inside its inference window. The first bracket "
            "begins after plan 3's nested owner-release receipt. This is temporal association, "
            "not proof of game consumption or physical key state."
        ),
        "limits": [
            "ammo digits in the video are manual visual transcriptions; no runtime ammo telemetry is available",
            "the encoded video is a 10 fps 2x export, so each transition is bounded to a 0.2-second source interval",
            "keys_held-to-step_completed is an execution lifecycle envelope, not exact physical key occupancy or game consumption",
            "the association does not establish causality, damage cause, successful targeting, or policy quality",
            "single failed retained trajectory; no game, model, GUI, OS input, or live allocation was run",
        ],
        "crop_files": {},
    }


def main():
    pins = json.loads(ANNOTATIONS.read_text())
    report_path, events_path = DATA / "report.json", DATA / "events.jsonl"
    video_path, sidecar_path = DATA / "map01-astra-live-01-2x.mp4", DATA / "video.json"
    video_sha = hashlib.sha256(video_path.read_bytes()).hexdigest()
    sidecar = json.loads(sidecar_path.read_text())
    if video_sha != sidecar["sha256"]:
        raise SystemExit("VIDEO_HASH_MISMATCH")
    report = json.loads(report_path.read_text())
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    frame_indices = set()
    for endpoint in pins["endpoint_samples"]:
        frame_indices.add(endpoint["video_frame"])
    for row in pins["decrements"]:
        frame_indices.update((row["before_frame"], row["after_frame"]))
    stream, frame_data = decode_crops(video_path, frame_indices, pins["ammo_roi_xyxy"])
    if stream.width != sidecar["width"] or stream.height != sidecar["height"] or stream.frames != sidecar["frames"]:
        raise SystemExit("VIDEO_STREAM_METADATA_MISMATCH")
    result = build(report, events, sidecar, pins, frame_data, video_sha)
    CROPS.mkdir(exist_ok=True)
    for index, row in frame_data.items():
        name = f"frame-{index:04d}-ammo.png"
        (CROPS / name).write_bytes(row["crop_png"])
        result["crop_files"][name] = digest_bytes(row["crop_png"])
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "disposition": result["disposition"],
        "transitions": result["ammo_decrement_count"],
        "overlap_cover_firing_steps": sum(bool(row["space_hold_lifecycle_overlaps"]) for row in result["transitions"]),
        "wholly_inside_plan4_model_window": result["ammo_decrements_during_plan4_model_window"],
        "straddling_model_start": result["ammo_decrements_straddling_plan4_model_start"],
        "before_model_start": result["ammo_decrements_before_plan4_model_start"],
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
