"""Audit refusal after a post-admission OpenTTD surface geometry change."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-framed-binding-fault-01"
TRIAL = ROOT / "fault"
SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    result = read(TRIAL / "result.json")
    assert report["case"] == result
    resolution = result["resolution"]
    moved = result["surface_move"]
    terminal = result["terminal"]
    assert resolution["target_geometry"] == [65, 40, 1152, 720]
    assert resolution["translation"] == [0, 0]
    assert moved["before"]["geometry"] == resolution["target_geometry"]
    assert moved["after"]["geometry"] == [82, 60, 1152, 720]
    assert resolution["emitted_ns"] < moved["emitted_ns"] < terminal["terminal_ns"]
    assert terminal["status"] == "needs_decision" and terminal["steps_completed"] == 1
    assert terminal["release"]["verified"] is True
    assert result["pointer_admissions"] == []
    assert result["bridge_exit_code"] == 0
    assert result["independent_evaluation"]["success"] is False
    assert result["independent_evaluation"]["checks"] == {
        "target_owned_roads": False,
        "ordered_bidirectional_connections": False,
        "forbidden_tiles_clear": True,
        "surrounding_road_owner_unchanged": True}
    assert result["independent_evaluation"]["changed_surrounding_tiles"] == []
    events = [json.loads(line) for line in
              (TRIAL / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    action = terminal["id"]
    action_events = [row for row in events if row.get("id") == action]
    assert not [row for row in action_events if row.get("event") == "pointer_admission"]
    assert [row["step"] for row in action_events if row.get("event") == "step_started"] == [0, 1]
    assert [row["step"] for row in action_events if row.get("event") == "step_completed"] == [0]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((TRIAL / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(TRIAL / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    assert read(TRIAL / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}
    assert read(TRIAL / "runtime/manifest.json")["save_sha256"] == SAVE_SHA
    audit = {"audit_passed": True,
        "resolved_target_geometry": resolution["target_geometry"],
        "post_admission_geometry": moved["after"]["geometry"],
        "terminal_status": terminal["status"],
        "pointer_admissions": 0,
        "move_to_terminal_ms": (terminal["terminal_ns"] - moved["emitted_ns"]) / 1e6,
        "submit_to_terminal_return_ms": result["submit_to_terminal_return_ms"],
        "exact_frames": len(observations), "durable_calls": result["durable_calls"],
        "release_verified": True, "all_owned_processes_exited": True,
        "save_unchanged": True, "independent_task_success": False,
        "decision": "RETAIN_LIVE_FRAME_RESOLUTION_WITH_POST-ADMISSION_GEOMETRY_REFUSAL",
        "scope": report["scope"]}
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
