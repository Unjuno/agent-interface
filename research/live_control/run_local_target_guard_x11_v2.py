"""Run the reversed-order target/guard X11 allocation."""
import json

from preregister_local_target_guard_x11_v2 import HERE, OUT, sha
from run_local_target_guard_x11_v1 import run_case


def main():
    plan = json.loads((OUT / "preregistration.json").read_text())
    assert plan["status"] == "preregistered_before_fresh_x11_execution"
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    rows = []
    for name in plan["order"]:
        rows.append(run_case(name, plan["allocations"][name], plan["condition"], OUT / name))
        (OUT / "execution.json").write_text(json.dumps(rows, indent=2) + "\n")
    passed = all(
        row["postcondition"] is not None and
        row["observed_visual_delta"] == plan["allocations"][row["name"]]["expected_visual_delta"] and
        row["postcondition"]["reason"] == plan["allocations"][row["name"]]["expected_reason"] and
        row["save_started"] is plan["allocations"][row["name"]]["save"] and
        row["terminal"]["release"]["verified"] is True
        for row in rows
    )
    report = {
        "passed": passed, "cases": rows,
        "decision": ("RETAIN_FRESH_TARGET_GUARD_INTEGRATION;_AUDIT_BEFORE_OPENTTD_TRANSFER" if passed else
                     "HOLD_TARGET_GUARD_INTEGRATION;_PRESERVE_REVERSED_FAILURE"),
        "scope": plan["scope"],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
