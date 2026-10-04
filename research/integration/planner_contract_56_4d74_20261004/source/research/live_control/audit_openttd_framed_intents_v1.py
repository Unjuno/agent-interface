"""Audit live binding-resolved framed intents on fresh OpenTTD cases."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from target_guard_from_paths_v1 import derive


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-framed-intents-01"
SOURCE = [129, 40, 1024, 720]
TARGET = [65, 40, 1152, 720]
FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
CONTINUATION = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]
SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def exact_frames(trial):
    runtime = trial / "runtime"
    events = [json.loads(line) for line in
              (runtime / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((runtime / f"{index:03d}.ait").read_bytes())
        with Image.open(runtime / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    return events, len(observations)


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["order"] == ["repeat", "target"]
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    expected = {
        "repeat": {"reason": "target_not_reached", "success": False,
                   "continuation": False, "target": [0, 0], "guard": [1, 1]},
        "target": {"reason": "met", "success": True,
                   "continuation": True, "target": [168, 168], "guard": [1, 1]},
    }
    rows = {}
    for result in report["cases"]:
        name = result["name"]
        trial = ROOT / name
        assert read(trial / "result.json") == result
        assert result["condition"]["reason"] == expected[name]["reason"]
        assert result["continuation_started"] is expected[name]["continuation"]
        assert result["independent_evaluation"]["success"] is expected[name]["success"]
        target = [row["target_changed_total"] for row in result["condition"]["measurements"]]
        guard = [row["guard_changed_total"] for row in result["condition"]["measurements"]]
        assert target == expected[name]["target"] and guard == expected[name]["guard"]
        assert result["terminal"]["release"]["verified"] is True
        assert result["bridge_exit_code"] == 0
        assert result["independent_evaluation"]["checks"]["forbidden_tiles_clear"] is True
        assert result["independent_evaluation"]["checks"]["surrounding_road_owner_unchanged"] is True
        assert result["independent_evaluation"]["changed_surrounding_tiles"] == []
        assert read(trial / "runtime/cleanup.json") == {
            "all_owned_processes_exited": True, "save_unchanged": True}
        assert read(trial / "runtime/manifest.json")["save_sha256"] == SAVE_SHA
        resolutions = result["resolution_records"]
        assert resolutions and all(row["source_geometry"] == SOURCE for row in resolutions)
        assert all(row["target_geometry"] == TARGET for row in resolutions)
        assert all(row["translation"] == ([0, 0] if row["coordinate_frame"] == "screen_chrome"
                                           else [-64, 0]) for row in resolutions)
        calls = read(trial / "calls.json")
        submit_steps = [call["result"]["request"]["command"]["steps"] for call in calls
                        if call["result"]["request"]["command"]["op"] == "submit"]
        guarded = submit_steps[-1]
        assert all(step.get("source_geometry") == SOURCE for step in guarded
                   if step.get("op", "").endswith("_in_frame"))
        framed_drags = [step for step in guarded if step.get("op") == "pointer_drag_in_frame"]
        assert framed_drags[0]["points"] == FIRST and framed_drags[-1]["points"] == CONTINUATION
        condition = next(step for step in guarded
                         if step.get("op") == "local_target_guard_postcondition_in_frame")
        boxes = derive(FIRST, CONTINUATION)
        assert condition["target_boxes"] == boxes["target_boxes"]
        assert condition["guard_boxes"] == boxes["guard_boxes"]
        events, frames = exact_frames(trial)
        emitted_resolutions = [row for row in events
                               if row.get("event") == "coordinate_frame_resolved"
                               and row.get("id") == result["terminal"]["id"]]
        assert emitted_resolutions == resolutions
        admitted_moves = [row["payload"] for row in events
                          if row.get("event") == "pointer_admission"
                          and row.get("operation") == "move"]
        resolved_first = [{"x": point["x"] - 64, "y": point["y"]} for point in FIRST]
        assert all(point in admitted_moves for point in resolved_first)
        assert FIRST[0] not in admitted_moves
        rows[name] = {"reason": expected[name]["reason"],
            "independent_success": expected[name]["success"],
            "continuation_started": expected[name]["continuation"],
            "resolution_records": len(resolutions), "exact_frames": frames,
            "drag_issued_to_condition_ms": result["drag_issued_to_condition_ms"],
            "durable_calls": result["durable_calls"]}
    audit = {"audit_passed": True, "cases": rows,
        "exact_frames": sum(row["exact_frames"] for row in rows.values()),
        "runtime_resolved_classifications": 2,
        "source_geometry": SOURCE, "live_target_geometry": TARGET,
        "runner_sent_source_coordinates_only": True,
        "resolved_pointer_admissions_verified": True,
        "release_verified": True, "all_owned_processes_exited": True,
        "save_unchanged": True,
        "decision": "RETAIN_LIVE_BINDING-RESOLVED_FRAMED_INTENTS;_NEXT_TEST_POST-ADMISSION_BINDING_CHANGE",
        "scope": report["scope"]}
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
