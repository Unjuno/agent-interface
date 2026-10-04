"""Audit the preregistered 1152x720 frame-specific transform replication."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from target_guard_from_paths_v1 import derive


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-guard-transform-04"
PRIOR = HERE / "results/openttd-target-guard-transform-03/audit.json"
SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"
FIRST = [{"x": 641, "y": 239}, {"x": 609, "y": 255}, {"x": 577, "y": 271}]
CONTINUATION = [{"x": 577, "y": 278}, {"x": 609, "y": 294}, {"x": 641, "y": 310}]


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


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["order"] == ["target", "repeat"]
    assert plan["predicted_target_pointer_geometry"] == [65, 40, 1152, 720]
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    expected = {
        "target": {"reason": "met", "success": True, "continuation": True,
                   "target": [168, 168], "guard": [1, 1]},
        "repeat": {"reason": "target_not_reached", "success": False,
                   "continuation": False, "target": [0, 0], "guard": [1, 1]},
    }
    rows = {}
    boxes = derive(FIRST, CONTINUATION)
    for result in report["cases"]:
        name = result["name"]
        trial = ROOT / name
        assert read(trial / "result.json") == result
        assert result["condition"]["reason"] == expected[name]["reason"]
        assert result["independent_evaluation"]["success"] is expected[name]["success"]
        assert result["continuation_started"] is expected[name]["continuation"]
        target = [sample["target_changed_total"] for sample in result["condition"]["measurements"]]
        guard = [sample["guard_changed_total"] for sample in result["condition"]["measurements"]]
        assert target == expected[name]["target"] and guard == expected[name]["guard"]
        assert result["coordinate_frames"] == {
            "screen_chrome_translation": [0, 0],
            "viewport_content_translation": [-64, 0]}
        assert result["terminal"]["release"]["verified"] is True
        assert result["bridge_exit_code"] == 0
        assert result["independent_evaluation"]["checks"]["forbidden_tiles_clear"] is True
        assert result["independent_evaluation"]["checks"]["surrounding_road_owner_unchanged"] is True
        assert result["independent_evaluation"]["changed_surrounding_tiles"] == []
        assert read(trial / "runtime/cleanup.json") == {
            "all_owned_processes_exited": True, "save_unchanged": True}
        assert read(trial / "runtime/manifest.json")["save_sha256"] == SAVE_SHA
        calls = read(trial / "calls.json")
        observations = [call["result"].get("state", {}).get("continuation", {}).get("observation")
                        for call in calls]
        geometries = [row["pointer_binding"]["geometry"] for row in observations if row]
        assert geometries and all(row == [65, 40, 1152, 720] for row in geometries)
        submissions = [call["result"]["request"]["command"]["steps"] for call in calls
                       if call["result"]["request"]["command"]["op"] == "submit"]
        guarded = submissions[-1]
        condition_index = 4 if name == "target" else 3
        first_index = 2 if name == "target" else 1
        continuation_index = 6 if name == "target" else 5
        assert guarded[first_index] == {"op": "pointer_drag", "points": FIRST,
                                        "duration_ms": 600}
        assert guarded[continuation_index] == {"op": "pointer_drag",
                                               "points": CONTINUATION, "duration_ms": 600}
        assert guarded[condition_index]["target_boxes"] == boxes["target_boxes"]
        assert guarded[condition_index]["guard_boxes"] == boxes["guard_boxes"]
        clicks = [step for step in guarded if step["op"] == "pointer_click"]
        if name == "target":
            assert clicks[0] == {"op": "pointer_click", "x": 820, "y": 51}
        assert {click["x"] for click in clicks}.issubset({709, 732, 820})
        rows[name] = {"reason": expected[name]["reason"],
            "independent_success": expected[name]["success"],
            "continuation_started": expected[name]["continuation"],
            "target_changed_totals": target, "guard_changed_totals": guard,
            "drag_issued_to_condition_ms": result["drag_issued_to_condition_ms"],
            "exact_frames": exact_frames(trial)}
    prior = read(PRIOR)
    prior_success = prior["studies"]["frame_specific_success"]
    audit = {"audit_passed": True,
        "predicted_and_observed_pointer_geometry": [65, 40, 1152, 720],
        "replication_cases": rows,
        "replication_exact_frames": sum(row["exact_frames"] for row in rows.values()),
        "corrected_two_resolution_classifications": 4,
        "corrected_two_resolution_exact_frames": prior_success["exact_frames"] +
            sum(row["exact_frames"] for row in rows.values()),
        "release_verified": True, "all_owned_processes_exited": True,
        "save_unchanged": True,
        "decision": "RETAIN_FRAME-SPECIFIC_RESOLUTION_TRANSFER_4_OF_4;_NEXT_REQUIRE_NEW_SAVE_OR_LIVE_BINDING-DERIVED_API",
        "scope": "two preregistered corrected positive/repeat pairs across 1280x720 and1152x720 on seed991004; no model, new save, human, token or general transform claim"}
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
