"""Join retained HUD-ammo changes to adjacent planner/action windows."""
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DATA = REPO / "research/doom/results/map01-astra-attempt-v1"


def reconstruct(report, events, failure, local_manifest, frame_manifest, image_root_exists):
    selected = report["decisions"][3:6]
    observations = {row["sequence"]: row for row in events
                    if row.get("event") == "observation" and row.get("sequence") in {117, 148, 211}}
    if set(observations) != {117, 148, 211}:
        raise ValueError("REQUIRED_AMMO_WINDOW_OBSERVATION_MISSING")
    if any(row.get("exact") is not True for row in observations.values()):
        raise ValueError("AMMO_ENDPOINT_NOT_EXACT")
    expected_names = ("117.png", "148.png", "211.png")
    for decision, expected in zip(selected, expected_names):
        if PurePosixPath(decision["source_image"]).name != expected:
            raise ValueError("DECISION_SOURCE_IMAGE_MISMATCH")
    for sequence, expected in zip((117, 148, 211), expected_names):
        if PurePosixPath(observations[sequence]["image"]).name != expected:
            raise ValueError("EVENT_SOURCE_IMAGE_MISMATCH")

    event_types = {row.get("event") for row in events}
    release_events = sorted(name for name in event_types
                            if "release" in str(name).lower() or "keyup" in str(name).lower() or "key_up" in str(name).lower())
    windows = []
    ammo = failure["visual_transcription"]["ammo"]
    frame_rows = {row["iteration"]: row for row in frame_manifest}
    for index, (left, right, left_sequence, right_sequence) in enumerate(
            ((selected[0], selected[1], 117, 148), (selected[1], selected[2], 148, 211)), start=3):
        plan_id = left["execution_trace"][0]["id"]
        key_rows = [row for row in events if row.get("event") == "keys_held" and row.get("id") == plan_id]
        held_keys = [key for row in key_rows for key in row.get("keys", [])]
        left_ammo, right_ammo = ammo[index], ammo[index + 1]
        windows.append({
            "from_decision": index,
            "to_decision": index + 1,
            "source_sequences": [left_sequence, right_sequence],
            "source_capture_ns": [observations[left_sequence]["capture_ns"], observations[right_sequence]["capture_ns"]],
            "source_capture_interval_ms": (observations[right_sequence]["capture_ns"] - observations[left_sequence]["capture_ns"]) / 1e6,
            "ammo_manual": [left_ammo, right_ammo],
            "ammo_delta": right_ammo - left_ammo,
            "planner_commands": left["action"].get("commands", []),
            "compiled_commands": left.get("compiled_commands", []),
            "plan_id": plan_id,
            "event_held_keys": held_keys,
            "controller_model_interval_ms": (left["controller_model_ended_ns"] - left["controller_model_started_ns"]) / 1e6,
            "controller_model_start_ns": left["controller_model_started_ns"],
            "controller_model_end_ns": left["controller_model_ended_ns"],
            "selected_frame_sha256": {str(index): frame_rows[index]["sha256"], str(index + 1): frame_rows[index + 1]["sha256"]},
        })
    anomaly = windows[1]
    return {
        "schema": "map01-astra-ammo-window-v1",
        "disposition": "PASS_POSTHOC_JOIN_HOLD_CAUSAL_ATTRIBUTION",
        "windows": windows,
        "nonfire_window_ammo_drop": anomaly["ammo_delta"],
        "nonfire_window_has_space_in_held_events": "space" in anomaly["event_held_keys"],
        "explicit_release_event_types_in_capture": release_events,
        "exact_intermediate_pngs_present": image_root_exists,
        "interpretation": "The 11-count manual ammo decrease is bracketed by exact observation events whose corresponding model plan is non-firing and whose keys_held summaries contain only Down and Right. The raw event schema has no explicit key-release event type. This is an attribution gap, not proof of an input leak or stale fire.",
        "limits": [
            "ammo labels are manual reads of selected frames, not typed runtime telemetry",
            "exact intermediate screenshot bytes are unavailable, so the count/time of individual shots is unknown",
            "keys_held summaries and plan terminal events do not prove physical key-up",
            "the interval spans planner latency and action execution; no causal attribution is possible",
            "single retained trajectory; no live experiment, recovery, task success, or MAP01 claim"
        ],
        "local_manifest_frame_count": len(local_manifest.get("frames", [])),
    }


def main():
    pins = json.loads((HERE / "AMMO_WINDOW_INPUTS.json").read_text())
    for relative, expected in pins["inputs"].items():
        actual = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"INPUT_HASH_MISMATCH {relative}")
    report = json.loads((DATA / "report.json").read_text())
    events = [json.loads(line) for line in (DATA / "events.jsonl").read_text().splitlines()]
    failure = json.loads((DATA / "failure-analysis-v1.json").read_text())
    manifest = json.loads((DATA / "local-exact-frame-manifest.json").read_text())
    frame_manifest = json.loads((DATA / "frame-manifest.json").read_text())
    result = reconstruct(report, events, failure, manifest, frame_manifest,
                         (REPO / manifest["retained_location"]).exists())
    result["input_sha256"] = pins["inputs"]
    (HERE / "AMMO_WINDOW_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"disposition": result["disposition"], "deltas": [row["ammo_delta"] for row in result["windows"]], "nonfire_window_keys": result["windows"][1]["event_held_keys"], "release_event_types": result["explicit_release_event_types_in_capture"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
