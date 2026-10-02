"""Independent raw-only oracle for the finite response-capacity fixture."""

import json
from pathlib import Path


EXPECTED_SCENARIOS = ("spare_capacity", "shared_saturation", "expired_lease", "handoff_not_accepted")
EXPECTED_ARMS = ("nominal_repertoire", "capacity_aware", "reserved_safety_lane")
FROZEN_FACTS = {
    "spare_capacity": {"now_ms": 10, "planner_busy_until_ms": 20, "threat_deadline_ms": 80,
                       "lease_expires_ms": 100, "handoff_offered": False, "handoff_accepted": False,
                       "release_lane_available": True},
    "shared_saturation": {"now_ms": 10, "planner_busy_until_ms": 120, "threat_deadline_ms": 80,
                          "lease_expires_ms": 100, "handoff_offered": False, "handoff_accepted": False,
                          "release_lane_available": False},
    "expired_lease": {"now_ms": 50, "planner_busy_until_ms": 50, "threat_deadline_ms": 80,
                      "lease_expires_ms": 40, "handoff_offered": False, "handoff_accepted": False,
                      "release_lane_available": True},
    "handoff_not_accepted": {"now_ms": 10, "planner_busy_until_ms": 120, "threat_deadline_ms": 80,
                             "lease_expires_ms": 100, "handoff_offered": True, "handoff_accepted": False,
                             "release_lane_available": False},
}


def expected_outcomes(facts, arm):
    replan_before_deadline = facts.get("planner_busy_until_ms", 10**12) <= facts.get("threat_deadline_ms", -1)
    authority_live = facts.get("now_ms", 10**12) < facts.get("lease_expires_ms", -1)
    human_can_respond = facts.get("handoff_offered") is True and facts.get("handoff_accepted") is True
    if arm == "nominal_repertoire":
        threat = "COVERED"  # The nominal matrix ignores contemporaneous capacity.
    else:
        threat = "COVERED" if ((replan_before_deadline and authority_live) or human_can_respond) else "NO_RESPONSE"
    release_available = arm == "nominal_repertoire" or arm == "reserved_safety_lane" or facts.get("release_lane_available") is True
    release = "COVERED" if release_available else "SAFE_STOP_ONLY"
    return {"threat_requires_replan": threat, "stuck_input_requires_release": release}


def audit(document):
    errors = []
    rows = document.get("rows", [])
    keys = set()
    expected_keys = {(scenario, arm) for scenario in EXPECTED_SCENARIOS for arm in EXPECTED_ARMS}
    for row in rows:
        key = (row.get("scenario_id"), row.get("arm"))
        if key in keys or key not in expected_keys:
            errors.append("invalid_or_duplicate_row:" + repr(key))
            continue
        keys.add(key)
        if row.get("facts") != FROZEN_FACTS.get(row.get("scenario_id")):
            errors.append("fixture_mutation:" + repr(key))
        outcomes = expected_outcomes(row.get("facts", {}), row.get("arm"))
        if row.get("outcomes") != outcomes:
            errors.append("outcome_mismatch:" + repr(key))
        if row.get("task_attainable") is not all(v == "COVERED" for v in outcomes.values()):
            errors.append("task_attainability_mismatch:" + repr(key))
        if row.get("authority_effect_applied") is not False:
            errors.append("effect_claimed:" + repr(key))
    if keys != expected_keys:
        errors.append("denominator_mismatch:" + str(len(keys)))
    if document.get("row_count") != len(expected_keys):
        errors.append("row_count_mismatch")

    by_key = {(r.get("scenario_id"), r.get("arm")): r for r in rows}
    nominal_saturated = by_key.get(("shared_saturation", "nominal_repertoire"), {}).get("task_attainable")
    aware_saturated = by_key.get(("shared_saturation", "capacity_aware"), {}).get("task_attainable")
    spare_aware = by_key.get(("spare_capacity", "capacity_aware"), {}).get("task_attainable")
    if nominal_saturated is not True or aware_saturated is not False:
        errors.append("saturation_false_coverage_not_detected")
    if spare_aware is not True:
        errors.append("spare_capacity_false_rejection")
    return {"decision": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "rows_expected": len(expected_keys), "rows_seen": len(keys), "errors": errors,
            "nominal_false_coverage_detected": nominal_saturated is True and aware_saturated is False,
            "spare_capacity_preserved": spare_aware is True}


def main():
    raw = json.loads(Path("candidate.raw.json").read_text(encoding="utf-8"))
    result = audit(raw)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
