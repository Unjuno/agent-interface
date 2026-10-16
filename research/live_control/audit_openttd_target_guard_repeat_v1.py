"""Audit the fresh seed991004 completed-segment repeat negative."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from target_guard_from_paths_v1 import derive


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-guard-repeat-01"
TRIAL = ROOT / "repeat"
SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"
FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
CONTINUATION = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["seed"] == 991004 and plan["allocation"] == "repeat"
    for name, expected in plan["sources"].items():
        assert sha(source_path(name)) == expected, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    result = read(TRIAL / "result.json")
    assert result["condition"]["reason"] == "target_not_reached"
    assert [sample["target_changed_pixels"] for sample in result["condition"]["measurements"]] == [
        [0, 0, 0], [0, 0, 0]]
    assert [sample["guard_changed_total"] for sample in result["condition"]["measurements"]] == [1, 1]
    assert result["steps_started"] == [0, 1, 2, 3]
    assert result["second_drag_started"] is False
    assert result["terminal"]["release"]["verified"] is True
    assert result["bridge_exit_code"] == 0
    assert result["independent_evaluation"]["success"] is False
    assert result["independent_evaluation"]["checks"] == {
        "target_owned_roads": False,
        "ordered_bidirectional_connections": False,
        "forbidden_tiles_clear": True,
        "surrounding_road_owner_unchanged": True,
    }
    assert result["independent_evaluation"]["changed_surrounding_tiles"] == []
    evaluation = read(TRIAL / "runtime/evaluation.json")
    for field in ("success", "checks", "changed_surrounding_tiles", "contract"):
        assert result["independent_evaluation"][field] == evaluation[field]
    tiles = {tile["id"]: tile for tile in evaluation["observation"]["tiles"]}
    assert all(tiles[tile]["road"] and tiles[tile]["owner"] == 0
               for tile in (684, 685, 686))
    assert all(not tiles[tile]["road"] and tiles[tile]["owner"] == -1
               for tile in (750, 814))
    assert read(TRIAL / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}
    manifest = read(TRIAL / "runtime/manifest.json")
    assert manifest["save_sha256"] == SAVE_SHA and "seed991004" in manifest["scope"]
    calls = read(TRIAL / "calls.json")
    submissions = [call["result"]["request"]["command"]["steps"] for call in calls
                   if call["result"]["request"]["command"]["op"] == "submit"]
    assert len(submissions) == 3
    assert submissions[1][2] == {"op": "pointer_drag", "points": FIRST,
                                  "duration_ms": 600}
    guarded = submissions[2]
    assert guarded[1] == {"op": "pointer_drag", "points": FIRST, "duration_ms": 600}
    assert guarded[5] == {"op": "pointer_drag", "points": CONTINUATION,
                          "duration_ms": 600}
    boxes = derive(FIRST, CONTINUATION)
    assert guarded[3]["target_boxes"] == boxes["target_boxes"]
    assert guarded[3]["guard_boxes"] == boxes["guard_boxes"]
    events = [json.loads(line) for line in
              (TRIAL / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((TRIAL / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(TRIAL / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    audit = {
        "audit_passed": True,
        "preregistered_result_passed": True,
        "prebuilt_target_tiles": [684, 685, 686],
        "unbuilt_continuation_tiles": [750, 814],
        "repeat_target_changed_totals": [0, 0],
        "repeat_guard_changed_totals": [1, 1],
        "continuation_suppressed": True,
        "independent_task_success": False,
        "independent_checks": result["independent_evaluation"]["checks"],
        "prebuild_submit_to_return_ms": result["prebuild_submit_to_return_ms"],
        "repeat_submit_to_return_ms": result["repeat_submit_to_return_ms"],
        "repeat_drag_issued_to_condition_ms": result["repeat_drag_issued_to_condition_ms"],
        "condition_to_terminal_ms": result["condition_to_terminal_ms"],
        "durable_calls": result["durable_calls"],
        "exact_frames": len(observations),
        "release_verified": True,
        "all_owned_processes_exited": True,
        "save_unchanged": True,
        "decision": "RETAIN_PATH-DERIVED_SEED991004_POSITIVE_AND_REPEAT-NEGATIVE;_NEXT_REQUIRE_HELD-OUT_SCREEN_TRANSFORM",
        "scope": report["scope"],
        "audit_sha256": sha(Path(__file__)),
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
