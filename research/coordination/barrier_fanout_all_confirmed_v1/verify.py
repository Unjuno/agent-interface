import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


def main():
    result = load("result.json")
    assert result["decision"] == "PASS_ALL_RECEIVER_BARRIER_CONFIRM_SCOPED"

    exact = load("coord_all_exact.json")
    changed = load("coord_one_changed.json")
    unavailable = load("coord_one_unavailable.json")
    changed_b = load("receiver_one_changed_B.json")
    unavailable_b = load("receiver_one_unavailable_B.json")

    assert exact["active_generation"] == 2
    assert changed["active_generation"] == 1
    assert unavailable["active_generation"] == 1
    assert changed_b["mode"] == "ACTIVE" and changed_b["accepted_generation"] == 1 and changed_b["revision"] == 2
    assert unavailable_b["mode"] == "BLOCKED" and unavailable_b["accepted_generation"] == 1 and unavailable_b["revision"] == 1

    totals = result["totals"]
    assert totals["initial_barrier_updates"] == 6
    assert totals["initial_barrier_update_successes"] == 6
    assert totals["classifier_real_gets"] == 5
    assert totals["classifier_fixture_unavailable"] == 1
    assert totals["receiver_recovery_puts"] == 0
    assert totals["coordination_updates"] == 1
    assert totals["global_all_confirmed"] == 1
    assert totals["global_hold_conflict"] == 1
    assert totals["global_hold_unknown"] == 1
    assert totals["timeout_inference_used"] is False
    assert totals["quorum_or_majority_rule_used"] is False

    print("PASS_ALL_RECEIVER_BARRIER_CONFIRM_SCOPED")


if __name__ == "__main__":
    main()
