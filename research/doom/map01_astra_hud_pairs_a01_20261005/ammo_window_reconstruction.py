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

    terminal_by_id = {row.get("id"): row for row in events
                      if row.get("event") == "terminal" and row.get("id")}
    windows = []
    ammo = failure["visual_transcription"]["ammo"]
    frame_rows = {row["iteration"]: row for row in frame_manifest}
    for index, (left, right, left_sequence, right_sequence) in enumerate(
            ((selected[0], selected[1], 117, 148), (selected[1], selected[2], 148, 211)), start=3):
        plan_id = left["execution_trace"][0]["id"]
        key_rows = [row for row in events if row.get("event") == "keys_held" and row.get("id") == plan_id]
        held_keys = [key for row in key_rows for key in row.get("keys", [])]
        terminal = terminal_by_id.get(plan_id)
        release = terminal.get("release") if terminal else None
        if not isinstance(release, dict) or release.get("event") != "owner_release":
            raise ValueError("OWNER_RELEASE_RECEIPT_MISSING")
        if release.get("verified") is not True or release.get("buttons_down") != [] or release.get("keys_down") != []:
            raise ValueError("OWNER_RELEASE_RECEIPT_NOT_CLEAR")
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
            "owner_release": {
                "event": release["event"], "reason": release.get("reason"),
                "verified": release["verified"], "buttons_down": release["buttons_down"],
                "keys_down": release["keys_down"], "verified_ns": release["verified_ns"],
                "terminal_ns": terminal["terminal_ns"],
                "capture_to_verified_release_ms": (release["verified_ns"] - observations[right_sequence]["capture_ns"]) / 1e6,
            },
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
        "standalone_release_event_type_count": sum(1 for row in events if row.get("event") == "owner_release"),
        "exact_intermediate_pngs_present": image_root_exists,
        "interpretation": "Both plans have nested verified owner_release receipts with empty buttons_down and keys_down. Sequence 148 was captured 97.359 ms before plan 3 release verification, and sequence 211 was captured 91.107 ms before plan 4 release verification. These are controller/owner-side receipts, not physical OS key-up or game-state samples. The 11-count manual ammo decrease occurred across the decision-4 window, but its timing and cause remain unknown; this is not proof of an input leak or stale fire.",
        "limits": [
            "ammo labels are manual reads of selected frames, not typed runtime telemetry",
            "exact intermediate screenshot bytes are unavailable, so the count/time of individual shots is unknown",
            "nested owner_release receipts document controller-side verification only; they do not prove physical OS key-up or actual game input state",
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
    print(json.dumps({"disposition": result["disposition"], "deltas": [row["ammo_delta"] for row in result["windows"]], "nonfire_window_keys": result["windows"][1]["event_held_keys"], "owner_release_verified": [row["owner_release"]["verified"] for row in result["windows"]], "capture_to_release_ms": [row["owner_release"]["capture_to_verified_release_ms"] for row in result["windows"]]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
