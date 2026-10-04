"""Audit the reverse-order fresh OpenTTD target/guard replication."""
import hashlib
import json
from pathlib import Path

from audit_openttd_target_guard_live_v2 import exact_frames, program_from_calls, read


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-guard-live-03"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["order"] == ["target", "wrong-row"]
    assert plan["unchanged_from_v2"].startswith("same runner")
    for name, expected in plan["sources"].items():
        assert sha(source_path(name)) == expected, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    rows = {}
    for name in plan["order"]:
        root = ROOT / name
        result = read(root / "result.json")
        assert read(root / "runtime/cleanup.json") == {
            "all_owned_processes_exited": True, "save_unchanged": True}
        assert result["bridge_exit_code"] == 0
        assert result["terminal"]["release"]["verified"] is True
        evaluation = read(root / "runtime/evaluation.json")
        for field in ("success", "checks", "changed_surrounding_tiles", "contract"):
            assert result["independent_evaluation"][field] == evaluation[field]
        program = program_from_calls(root)
        assert program[:2] == [
            {"op": "pointer_click", "x": 820, "y": 51},
            {"op": "pointer_click", "x": 709, "y": 91},
        ]
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
    target, wrong = rows["target"], rows["wrong-row"]
    assert target["condition_reason"] == "met"
    assert target["target_changed_totals"] == [170, 170]
    assert target["guard_changed_totals"] == [0, 0]
    assert target["second_drag_started"] is True
    assert target["independent_success"] is True and all(target["checks"].values())
    assert wrong["condition_reason"] == "target_not_reached"
    assert wrong["target_changed_totals"] == [17, 17]
    assert wrong["guard_changed_totals"] == [0, 0]
    assert wrong["second_drag_started"] is False
    assert wrong["independent_success"] is False
    prior = read(HERE / "results/openttd-target-guard-live-02/audit.json")
    assert prior["audit_passed"] is True
    for name in ("target", "wrong-row"):
        for field in ("condition_reason", "target_changed_totals", "guard_changed_totals",
                      "second_drag_started", "independent_success", "checks"):
            assert rows[name][field] == prior["cases"][name][field]
    audit = {
        "audit_passed": True,
        "preregistered_result_passed": True,
        "reverse_order_reproduced_v2": True,
        "cases": rows,
        "exact_frames": sum(row["exact_frames"] for row in rows.values()),
        "cumulative_fresh_corrected_pairs": 2,
        "cumulative_expected_classifications": 4,
        "all_terminal_releases_verified": True,
        "all_owned_processes_exited": True,
        "save_unchanged": True,
        "decision": "PROMOTE_AS_SAME-SEED_SCRIPTED_OPENTTD_LOCAL_CONTINUATION_CANDIDATE;_REQUIRE_NEW_GEOMETRY_AND_MODEL-AUTHORED_BOXES_FOR_GENERALIZATION",
        "scope": report["scope"],
        "audit_sha256": sha(Path(__file__)),
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
