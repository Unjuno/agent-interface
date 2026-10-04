"""Audit the one-click-corrected fresh OpenTTD target/guard pair."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-guard-live-02"


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


def program_from_calls(root):
    calls = read(root / "calls.json")
    submitted = [call["result"]["request"]["command"] for call in calls
                 if call["result"]["request"]["command"]["op"] == "submit"]
    return next(command["steps"] for command in submitted
                if any(step.get("op") == "local_target_guard_postcondition"
                       for step in command["steps"]))


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["single_change_from_retained_v1"].startswith("prepend pointer_click(820,51)")
    for name, expected in plan["sources"].items():
        assert sha(source_path(name)) == expected, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    rows = {}
    for name in plan["order"]:
        root = ROOT / name
        result = read(root / "result.json")
        cleanup = read(root / "runtime/cleanup.json")
        assert cleanup == {"all_owned_processes_exited": True, "save_unchanged": True}
        assert result["bridge_exit_code"] == 0
        assert result["terminal"]["release"]["verified"] is True
        assert result["program_submit_to_return_ms"] > 0
        assert result["first_drag_issued_to_condition_ms"] > 0
        assert result["condition_to_terminal_ms"] >= 0
        evaluation = read(root / "runtime/evaluation.json")
        for field in ("success", "checks", "changed_surrounding_tiles", "contract"):
            assert result["independent_evaluation"][field] == evaluation[field]
        program = program_from_calls(root)
        assert program[:2] == [
            {"op": "pointer_click", "x": 820, "y": 51},
            {"op": "pointer_click", "x": 709, "y": 91},
        ]
        assert program[4]["op"] == "local_target_guard_postcondition"
        assert program[4]["target_boxes"] == [[699, 236, 12, 8], [667, 252, 12, 8],
                                                [635, 268, 12, 8]]
        assert program[4]["guard_boxes"] == [[667, 284, 12, 8], [699, 300, 12, 8]]
        rows[name] = {
            "exact_frames": exact_frames(root),
            "condition_reason": result["condition"]["reason"],
            "target_changed_totals": [sample["target_changed_total"]
                                      for sample in result["condition"]["measurements"]],
            "guard_changed_totals": [sample["guard_changed_total"]
                                     for sample in result["condition"]["measurements"]],
            "second_drag_started": result["second_drag_started"],
            "independent_success": result["independent_evaluation"]["success"],
            "checks": result["independent_evaluation"]["checks"],
            "program_submit_to_return_ms": result["program_submit_to_return_ms"],
            "first_drag_issued_to_condition_ms": result["first_drag_issued_to_condition_ms"],
            "condition_to_terminal_ms": result["condition_to_terminal_ms"],
            "durable_calls": result["durable_calls"],
        }
    wrong = rows["wrong-row"]
    assert wrong["condition_reason"] == "target_not_reached"
    assert wrong["target_changed_totals"] == [17, 17]
    assert wrong["guard_changed_totals"] == [0, 0]
    assert wrong["second_drag_started"] is False
    assert wrong["independent_success"] is False
    target = rows["target"]
    assert target["condition_reason"] == "met"
    assert target["target_changed_totals"] == [170, 170]
    assert target["guard_changed_totals"] == [0, 0]
    assert target["second_drag_started"] is True
    assert target["independent_success"] is True
    assert all(target["checks"].values())
    audit = {
        "audit_passed": True,
        "preregistered_result_passed": True,
        "one_click_driver_correction": "road toolbar opened at (820,51) before unchanged direction selection and drags",
        "cases": rows,
        "exact_frames": sum(row["exact_frames"] for row in rows.values()),
        "all_terminal_releases_verified": True,
        "all_owned_processes_exited": True,
        "save_unchanged": True,
        "decision": "RETAIN_FRESH_OPENTTD_TARGET_GUARD_PAIR;_REPLICATE_BEFORE_PROMOTION",
        "scope": report["scope"],
        "audit_sha256": sha(Path(__file__)),
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
