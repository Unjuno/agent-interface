#!/usr/bin/env python3
"""Small non-formal smoke checks; never emits the formal raw corpus."""
from simulate import run_arm


def scenario(workers, order, delay, condition, outcome):
    return {"workers": workers, "order": order,
            "observation_delay": delay,
            "marker_condition": condition,
            "owner_outcome": outcome}


def events(row, name):
    return [event for event in row["trace"] if event.get("event") == name]


def main():
    checks = []
    # Crash must retain the original lease through tick 3; recovery is tick 4.
    row = run_arm(scenario(2, [0, 1], 0, "clean", "crash"), "NONE")
    grants = events(row, "lease_grant")
    releases = [e for e in events(row, "lease_release") if e.get("cause") == "lease_expired"]
    assert grants[0]["until"] == 3
    assert releases[0]["tick"] == 3
    assert grants[1]["tick"] == 4
    assert row["counts"]["recoveries"] == 1
    assert row["counts"]["completed_tasks"] == 1
    checks.append("crash_ttl3_recovery_tick4")

    # At expiry equality, a worker may acquire, but the marker must not suppress.
    row = run_arm(scenario(4, [0, 1, 2, 3], 0, "clean", "crash"), "LOCAL_MARKERS")
    assert any(e.get("tick") == 3 for e in events(row, "lease_grant"))
    assert not any(e.get("tick") >= 3 for e in events(row, "proposal_suppressed"))
    checks.append("expiry_equality_admits_without_marker_suppression")

    # Visibility delays at and beyond expiry yield no suppressing hints.
    for delay in (3, 4):
        row = run_arm(scenario(4, [0, 1, 2, 3], delay, "clean", "crash"), "LOCAL_MARKERS")
        assert not events(row, "proposal_suppressed")
    checks.append("delay3_and4_no_suppression")

    row = run_arm(scenario(3, [0, 1, 2], 1, "duplicated", "complete"), "LOCAL_MARKERS")
    assert all(e.get("copies") == 2 for e in events(row, "marker_observed"))
    checks.append("duplicate_marker_reduced_advisory")

    for condition in ("stale", "forged"):
        row = run_arm(scenario(3, [0, 1, 2], 0, condition, "crash"), "LOCAL_MARKERS")
        assert len(events(row, "marker_rejected")) == 2
        assert row["counts"]["recoveries"] == 1
    checks.append("stale_and_forged_controls_fail_closed")

    print("construction PASS: " + ", ".join(checks))


if __name__ == "__main__":
    main()
