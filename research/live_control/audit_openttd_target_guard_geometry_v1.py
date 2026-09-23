"""Audit the seed991004 path-derived pair and its aliased negative control."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-guard-geometry-01"
SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def exact_frames(root):
    events = [json.loads(line) for line in (root / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    return len(observations)


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["seed"] == 991004 and plan["order"] == ["wrong-row", "target"]
    for name, expected in plan["sources"].items():
        assert sha(source_path(name)) == expected, name
    report = read(ROOT / "report.json")
    assert report["passed"] is False
    rows = {}
    for name in plan["order"]:
        root = ROOT / name
        result = read(root / "result.json")
        assert read(root / "runtime/cleanup.json") == {
            "all_owned_processes_exited": True, "save_unchanged": True}
        manifest = read(root / "runtime/manifest.json")
        assert manifest["save_sha256"] == SAVE_SHA
        assert "seed991004" in manifest["scope"]
        assert result["bridge_exit_code"] == 0
        assert result["terminal"]["release"]["verified"] is True
        assert result["condition"]["reason"] == "met"
        assert result["second_drag_started"] is True
        assert result["independent_evaluation"]["success"] is True
        assert all(result["independent_evaluation"]["checks"].values())
        evaluation = read(root / "runtime/evaluation.json")
        for field in ("success", "checks", "changed_surrounding_tiles", "contract"):
            assert result["independent_evaluation"][field] == evaluation[field]
        rows[name] = {
            "first_y_offset": result["first_y_offset"],
            "condition_reason": result["condition"]["reason"],
            "target_changed_totals": [sample["target_changed_total"]
                                      for sample in result["condition"]["measurements"]],
            "guard_changed_totals": [sample["guard_changed_total"]
                                     for sample in result["condition"]["measurements"]],
            "second_drag_started": result["second_drag_started"],
            "independent_success": result["independent_evaluation"]["success"],
            "checks": result["independent_evaluation"]["checks"],
            "exact_frames": exact_frames(root),
            "program_submit_to_return_ms": result["program_submit_to_return_ms"],
            "first_drag_issued_to_condition_ms": result["first_drag_issued_to_condition_ms"],
        }
    assert rows["wrong-row"]["first_y_offset"] == -16
    assert rows["wrong-row"]["target_changed_totals"] == [166, 166]
    assert rows["target"]["first_y_offset"] == 0
    assert rows["target"]["target_changed_totals"] == [168, 168]
    audit = {
        "audit_passed": True,
        "preregistered_result_passed": False,
        "cases": rows,
        "diagnosis": "the -16px first path aliases to the same intended OpenTTD A-to-B tiles under seed991004 tile snapping",
        "candidate_interpretation": "both local met outcomes agree with both independent successes; the preregistered negative-input assumption failed",
        "decision": "PRESERVE_NEGATIVE-CONTROL_FAILURE;_USE_COMPLETED-SEGMENT_REPEAT_AS_SEPARATELY_PREREGISTERED_NEGATIVE",
        "scope": report["scope"],
        "audit_sha256": sha(Path(__file__)),
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
