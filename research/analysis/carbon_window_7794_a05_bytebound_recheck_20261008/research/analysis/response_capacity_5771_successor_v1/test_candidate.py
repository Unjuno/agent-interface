import copy

import candidate
import audit


def test_capacity_aware_rule_separates_nominal_and_available_responses():
    raw = candidate.run()
    result = audit.audit(raw)
    assert result["decision"] == "PASS_METHOD_SCOPED"
    assert result["nominal_false_coverage_detected"]
    assert result["spare_capacity_preserved"]


def test_safety_release_lane_does_not_claim_task_completion():
    row = next(r for r in candidate.run()["rows"] if r["scenario_id"] == "shared_saturation" and r["arm"] == "reserved_safety_lane")
    assert row["outcomes"]["stuck_input_requires_release"] == "COVERED"
    assert row["outcomes"]["threat_requires_replan"] == "NO_RESPONSE"
    assert row["task_attainable"] is False


def test_unaccepted_handoff_is_not_capacity():
    raw = candidate.run()
    row = next(r for r in raw["rows"] if r["scenario_id"] == "handoff_not_accepted" and r["arm"] == "capacity_aware")
    assert row["outcomes"]["threat_requires_replan"] == "NO_RESPONSE"


def test_audit_rejects_missing_row_and_authority_mutation():
    raw = candidate.run()
    dropped = copy.deepcopy(raw)
    dropped["rows"].pop()
    assert audit.audit(dropped)["decision"] == "FAIL_AUDIT"
    forged = copy.deepcopy(raw)
    forged["rows"][0]["authority_effect_applied"] = True
    assert audit.audit(forged)["decision"] == "FAIL_AUDIT"
