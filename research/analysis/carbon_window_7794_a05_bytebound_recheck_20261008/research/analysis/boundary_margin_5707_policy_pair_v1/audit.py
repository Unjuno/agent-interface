#!/usr/bin/env python3
"""Independent raw-only T0 auditor. Does not import the runner."""
import json
import sys

IDS = ["opp-01", "opp-02", "opp-03", "opp-04"]
BOUNDARIES = [100, 200, 300, 400]
HAZARDS = [110, 210, 310, 410]
EVENTS = ["evt-01", "evt-02", "evt-03", "evt-04"]
EARLY = [40, 140, 240, 340]
LATE = [90, 190, 290, 390]
CASES = ["matched_policy_pair", "crossing", "safe_stop", "missing_time", "altered_opportunities", "equality"]


def audit(rows):
    errors = []
    if [row.get("case") for row in rows] != CASES:
        return ["case_order_or_count"]
    pair = rows[0]
    if pair.get("disposition") != "OBSERVED" or pair.get("exogenous") != [
        {"id": i, "boundary_ms": b, "hazard_ms": h, "event_id": e}
        for i, b, h, e in zip(IDS, BOUNDARIES, HAZARDS, EVENTS)
    ]:
        errors.append("frozen_exogenous_schedule")
    arms = pair.get("arms", [])
    if [arm.get("name") for arm in arms] != ["early", "late"]:
        errors.append("policy_identity")
    else:
        computed = []
        for arm, schedule in zip(arms, (EARLY, LATE)):
            records = arm.get("opportunities", [])
            if [r.get("id") for r in records] != IDS:
                errors.append(arm["name"] + ":opportunity_identity")
            margins = []
            for i, (rec, admission, boundary, hazard, event) in enumerate(zip(records, schedule, BOUNDARIES, HAZARDS, EVENTS)):
                margin = boundary - admission
                margins.append(margin)
                if rec != {"id": IDS[i], "admission_ms": admission, "margin_ms": margin, "event_id": event,
                           "hazard_ms": hazard, "forbidden_effect": False}:
                    errors.append(arm["name"] + ":policy_margin_or_external_event:" + IDS[i])
            computed.append(margins)
        if len(computed) == 2 and (min(computed[0]) != 60 or min(computed[1]) != 10 or min(computed[0]) - min(computed[1]) != 50):
            errors.append("paired_margin_contrast")
        if len(arms) == 2:
            counts = [sum(r.get("forbidden_effect") is True for r in a.get("opportunities", [])) for a in arms]
            if counts != [0, 0] or [len(a.get("opportunities", [])) for a in arms] != [4, 4]:
                errors.append("paired_event_or_denominator_counts")
    cross = rows[1]
    if cross.get("admission_ms") is None or cross.get("margin_ms") != cross["opportunity"].get("boundary_ms") - cross["admission_ms"] or cross.get("margin_ms") != -3 or cross.get("forbidden_effect") is not True or cross.get("disposition") != "BOUNDARY_CROSSED":
        errors.append("crossing_control")
    stop = rows[2]
    if stop.get("stopped") is not True or stop.get("downstream_outcome") != "UNKNOWN" or stop.get("disposition") != "STOP_RECORDED_OUTCOME_UNKNOWN":
        errors.append("safe_stop_control")
    missing = rows[3]
    if missing.get("admission_ms") is not None or missing.get("margin_ms") is not None or missing.get("disposition") != "UNKNOWN":
        errors.append("missing_time_control")
    altered = rows[4]
    if altered.get("early_ids") == altered.get("late_ids") or altered.get("disposition") != "HOLD_NO_STABLE_DENOMINATOR":
        errors.append("denominator_control")
    equality = rows[5]
    if equality.get("margin_ms") != 0 or equality.get("forbidden_effect") is not False or equality.get("disposition") != "ZERO_MARGIN_NOT_CROSSED":
        errors.append("equality_control")
    return errors


def main(path):
    with open(path, encoding="utf-8") as source:
        records = [json.loads(line) for line in source if line.strip()]
    errors = audit(records)
    print(json.dumps({"rows": len(records), "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "errors": errors}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
