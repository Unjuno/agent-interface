"""Audit two retained transform failures and the frame-specific repair."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from target_guard_from_paths_v1 import derive


HERE = Path(__file__).resolve().parent
SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"
BASE_FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
BASE_CONTINUATION = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]


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
        assert image.size == (1280, 800)
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    return len(observations)


def observation_geometries(calls):
    values = []
    for call in calls:
        observation = call["result"].get("state", {}).get("continuation", {}).get("observation")
        if observation:
            values.append(observation["pointer_binding"]["geometry"])
    return values


def submissions(calls):
    return [call["result"]["request"]["command"]["steps"] for call in calls
            if call["result"]["request"]["command"]["op"] == "submit"]


def audit_study(number, expected):
    root = HERE / f"results/openttd-target-guard-transform-0{number}"
    plan = read(root / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, f"study {number}: {name}"
    report = read(root / "report.json")
    assert report["passed"] is expected["passed"]
    assert [row["name"] for row in report["cases"]] == plan["order"]
    rows = {}
    for result in report["cases"]:
        name = result["name"]
        trial = root / name
        stored = read(trial / "result.json")
        assert stored == result
        assert result["condition"]["reason"] == expected[name]["reason"]
        assert result["continuation_started"] is expected[name]["continuation"]
        assert result["independent_evaluation"]["success"] is expected[name]["success"]
        assert result["terminal"]["release"]["verified"] is True
        assert result["bridge_exit_code"] == 0
        assert result["independent_evaluation"]["checks"]["forbidden_tiles_clear"] is True
        assert result["independent_evaluation"]["checks"]["surrounding_road_owner_unchanged"] is True
        assert result["independent_evaluation"]["changed_surrounding_tiles"] == []
        assert read(trial / "runtime/cleanup.json") == {
            "all_owned_processes_exited": True, "save_unchanged": True}
        assert read(trial / "runtime/manifest.json")["save_sha256"] == SAVE_SHA
        calls = read(trial / "calls.json")
        assert all(geometry == [1, 40, 1280, 720]
                   for geometry in observation_geometries(calls))
        frames = exact_frames(trial)
        rows[name] = {
            "reason": result["condition"]["reason"],
            "target_changed_totals": [sample["target_changed_total"]
                                      for sample in result["condition"]["measurements"]],
            "guard_changed_totals": [sample["guard_changed_total"]
                                     for sample in result["condition"]["measurements"]],
            "continuation_started": result["continuation_started"],
            "independent_success": result["independent_evaluation"]["success"],
            "drag_issued_to_condition_ms": result["drag_issued_to_condition_ms"],
            "exact_frames": frames,
        }
    return {"passed": report["passed"], "cases": rows,
            "exact_frames": sum(row["exact_frames"] for row in rows.values())}


def main():
    old_calls = read(HERE / "results/openttd-target-guard-geometry-01/target/calls.json")
    new_calls = read(HERE / "results/openttd-target-guard-transform-01/target/calls.json")
    old_geometry = observation_geometries(old_calls)[0]
    new_geometry = observation_geometries(new_calls)[0]
    assert old_geometry == [129, 40, 1024, 720]
    assert new_geometry == [1, 40, 1280, 720]
    assert [new_geometry[0] - old_geometry[0], new_geometry[1] - old_geometry[1]] == [-128, 0]
    audits = {
        "global_positive_128_failure": audit_study(1, {
            "passed": False,
            "repeat": {"reason": "target_not_reached", "continuation": False, "success": False},
            "target": {"reason": "target_not_reached", "continuation": False, "success": False}}),
        "global_negative_128_failure": audit_study(2, {
            "passed": False,
            "target": {"reason": "guard_changed", "continuation": False, "success": False},
            "repeat": {"reason": "target_not_reached", "continuation": False, "success": False}}),
        "frame_specific_success": audit_study(3, {
            "passed": True,
            "repeat": {"reason": "target_not_reached", "continuation": False, "success": False},
            "target": {"reason": "met", "continuation": True, "success": True}}),
    }
    repaired_root = HERE / "results/openttd-target-guard-transform-03"
    for name in ("repeat", "target"):
        result = read(repaired_root / name / "result.json")
        assert result["coordinate_frames"] == {
            "screen_chrome_translation": [0, 0],
            "viewport_content_translation": [-128, 0]}
        paths = submissions(read(repaired_root / name / "calls.json"))
        guarded = paths[-1]
        condition_index = 3 if name == "repeat" else 4
        first_index = 1 if name == "repeat" else 2
        continuation_index = 5 if name == "repeat" else 6
        first = [{"x": point["x"] - 128, "y": point["y"]} for point in BASE_FIRST]
        continuation = [{"x": point["x"] - 128, "y": point["y"]}
                        for point in BASE_CONTINUATION]
        assert guarded[first_index] == {"op": "pointer_drag", "points": first,
                                        "duration_ms": 600}
        assert guarded[continuation_index] == {"op": "pointer_drag", "points": continuation,
                                               "duration_ms": 600}
        boxes = derive(first, continuation)
        assert guarded[condition_index]["target_boxes"] == boxes["target_boxes"]
        assert guarded[condition_index]["guard_boxes"] == boxes["guard_boxes"]
        chrome_clicks = [step for step in guarded if step["op"] == "pointer_click"]
        if name == "target":
            assert chrome_clicks[0] == {"op": "pointer_click", "x": 820, "y": 51}
        assert {click["x"] for click in chrome_clicks}.issubset({709, 732, 820})
    audit = {"audit_passed": True,
        "source_pointer_geometry": old_geometry,
        "target_pointer_geometry": new_geometry,
        "window_origin_delta": [-128, 0],
        "studies": audits,
        "total_exact_frames": sum(study["exact_frames"] for study in audits.values()),
        "decision": "RETAIN_FRAME-SPECIFIC_TRANSFORM;_REPLICATE_ON_A_SECOND_RESOLUTION_OR_WINDOW_POSITION",
        "scope": "two retained fresh failures and one fresh corrected pair on seed991004; resolution transfer only, no model, unseen task, human, token or broad transform claim"}
    (repaired_root / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
