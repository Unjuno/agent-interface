#!/usr/bin/env python3
"""Independent arithmetic audit of the one frozen guard-boundary result."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    expected = []
    source_health = fixture["source"]["health"]["value"]
    hard_min = fixture["authored_health_hard_minimum"]
    for sample in fixture["samples"]:
        expected.append(sample["health"] < hard_min)
    actual = [row["would_request_new_decision"] for row in result["observations"]]
    # The guard's frozen spec is health-only. The independent expected result
    # reflects that contract, while separately checking the fire/ammo mismatch.
    health_only_expected = [False, False, True]
    checks = {
        "fixture_has_fire_cover": any(x["action"] in {"fire", "advance_fire", "retreat_fire"}
                                       for x in fixture["notional_active_cover"]),
        "result_has_three_observations": len(result["observations"]) == 3,
        "health_only_monitor_reconstruction": actual == health_only_expected,
        "positive_control_preserved": actual[0] is False,
        "ammo_zero_not_invalidated": actual[1] is False and
                                     fixture["samples"][1]["ammo"] == 0 and
                                     source_health >= hard_min,
        "health_hard_floor_control_invalidated": actual[2] is True and expected[2] is True,
        "no_live_allocation_invoked": result["formal_live_allocation_invocations"] == 0,
    }
    audit = {"format": "59-v39-ammo-cover-audit-v1", "checks": checks,
             "passed": sum(checks.values()), "total": len(checks),
             "disposition": "FAIL_AMMO_DEPLETION_NOT_GUARDED"
             if all(checks.values()) and not actual[1] else "AUDIT_FAILED"}
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True,
                                      separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
