"""Audit the retained fresh OpenTTD target/guard driver failure."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-guard-live-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def main():
    plan = read(ROOT / "preregistration.json")
    for name, expected in plan["sources"].items():
        assert sha(source_path(name)) == expected, name
    report = read(ROOT / "report.json")
    assert report["passed"] is False
    cases = {}
    for name in plan["order"]:
        root = ROOT / name
        result = read(root / "result.json")
        events = [json.loads(line) for line in (root / "runtime/events.jsonl").read_text().splitlines()]
        observations = [row for row in events if row.get("event") == "observation"]
        decoder = Decoder("live-control")
        for index, observation in enumerate(observations, 1):
            frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
            with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
                image = opened.convert("RGB")
            assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
        cleanup = read(root / "runtime/cleanup.json")
        assert cleanup == {"all_owned_processes_exited": True, "save_unchanged": True}
        assert result["bridge_exit_code"] == 0
        assert result["terminal"]["release"]["verified"] is True
        assert result["steps_started"] == [0, 1, 2, 3]
        assert result["second_drag_started"] is False
        assert result["condition"]["reason"] == "target_not_reached"
        assert result["independent_evaluation"]["success"] is False
        assert result["independent_evaluation"]["checks"] == {
            "target_owned_roads": False,
            "ordered_bidirectional_connections": False,
            "forbidden_tiles_clear": True,
            "surrounding_road_owner_unchanged": True,
        }
        evaluation = read(root / "runtime/evaluation.json")
        for field in ("success", "checks", "changed_surrounding_tiles", "contract"):
            assert result["independent_evaluation"][field] == evaluation[field]
        calls = read(root / "calls.json")
        submitted = [call["result"]["request"]["command"] for call in calls
                     if call["result"]["request"]["command"]["op"] == "submit"]
        program = next(command["steps"] for command in submitted
                       if any(step.get("op") == "local_target_guard_postcondition"
                              for step in command["steps"]))
        assert program[0] == {"op": "pointer_click", "x": 709, "y": 91}
        assert not any(step.get("op") == "pointer_click" and step.get("x") == 820
                       and step.get("y") == 51 for step in program)
        cases[name] = {
            "exact_frames": len(observations),
            "condition_reason": result["condition"]["reason"],
            "target_changed_totals": [sample["target_changed_total"]
                                      for sample in result["condition"]["measurements"]],
            "second_drag_started": False,
            "independent_success": False,
            "release_verified": True,
        }
    audit = {
        "audit_passed": True,
        "preregistered_result_passed": False,
        "cases": cases,
        "diagnosis": "driver omitted the road-toolbar opener at (820,51) before selecting the first road tool at (709,91)",
        "evidence_limit": "the run proves a driver-boundary failure and safe stop; it does not evaluate the target/guard condition after successful OpenTTD road actuation",
        "decision": "PRESERVE_FAILURE;_RETEST_ONLY_AS_SEPARATELY_PREREGISTERED_ONE-CLICK_DRIVER_CORRECTION",
        "scope": report["scope"],
        "audit_sha256": sha(Path(__file__)),
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
