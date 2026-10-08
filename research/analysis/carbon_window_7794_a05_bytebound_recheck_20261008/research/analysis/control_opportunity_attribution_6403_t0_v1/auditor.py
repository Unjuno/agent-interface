"""Independent evidence-only audit for the Issue #6403 T0 fixture."""
import json
import sys


def independently_classify(row):
    status = row.get("delivery_status")
    if status == "AMBIGUOUS":
        return "UNKNOWN"
    if (row.get("agent_action_at") is not None and row.get("effect_at") is not None
            and row["agent_action_at"] < row["effect_at"] and row.get("sent_at") is not None
            and row["sent_at"] >= row["effect_at"]):
        return "NO_OPPORTUNITY"
    if status == "NOT_DELIVERED":
        return "NO_OPPORTUNITY"
    delivered = row.get("delivered_at")
    effected = row.get("effect_at")
    accepted = row.get("accepted_at")
    if delivered is None or effected is None or accepted is None:
        return "UNKNOWN"
    if delivered >= effected or accepted >= effected:
        return "NO_OPPORTUNITY"
    if any(row.get(key) is None for key in (
        "safe_override_available", "override_authorized", "ui_current"
    )):
        return "UNKNOWN"
    if not (row["safe_override_available"] and row["override_authorized"] and row["ui_current"]):
        return "NO_OPPORTUNITY"
    ready = delivered if delivered >= accepted else accepted
    if effected - ready < row["override_duration"]:
        return "NO_OPPORTUNITY"
    corrected = row.get("correction_at")
    if row.get("correction_verified") is True and corrected is not None and ready <= corrected < effected:
        return "OPPORTUNITY_USED"
    return "OPPORTUNITY"


def independently_reconstruct(row):
    items = [
        (row.get("agent_action_at"), "agent_action"),
        (row.get("sent_at"), "notification_sent"),
        (row.get("delivered_at"), "notification_delivery"),
        (row.get("accepted_at"), "handoff_accepted"),
        (row.get("effect_at"), "agent_effect"),
        (row.get("correction_at"), "human_correction"),
    ]
    timeline = []
    for at, event in sorted(items, key=lambda pair: (pair[0] is None, pair[0] or 0)):
        if at is None:
            continue
        if event == "agent_action":
            timeline.append({"event": event, "at": at, "authority_holder": row["authority_holder"]})
        elif event == "notification_sent":
            timeline.append({"event": event, "at": at})
        elif event == "notification_delivery":
            timeline.append({"event": event, "status": row["delivery_status"], "at": at})
        elif event == "agent_effect":
            timeline.append({"event": event, "at": at, "effect": row["effect"]})
        elif event == "human_correction":
            timeline.append({"event": event, "at": at, "verified": row["correction_verified"]})
        else:
            timeline.append({"event": event, "at": at})
    return timeline


def audit(fixture, oracle, candidate):
    failures = []
    raw_by_id = {row["id"]: row for row in fixture["traces"]}
    expected = oracle["expected"]
    actual_by_id = {row["trace"]: row for row in candidate.get("records", [])}
    if set(actual_by_id) != set(raw_by_id) or set(expected) != set(raw_by_id):
        failures.append("trace coverage mismatch")
    for trace_id, raw in raw_by_id.items():
        out = actual_by_id.get(trace_id)
        if out is None:
            continue
        recomputed = independently_classify(raw)
        if recomputed != expected.get(trace_id):
            failures.append(f"oracle disagrees with independent evidence reconstruction: {trace_id}")
        if out.get("assessment") != recomputed:
            failures.append(f"candidate assessment mismatch: {trace_id}")
        for key in ("actor_outcome_summary", "control_timeline_summary"):
            summary = out.get(key, {})
            if summary.get("accessible_fact_ids") != fixture["presentation_fact_ids"]:
                failures.append(f"unequal or altered factual access: {trace_id}/{key}")
            if summary.get("raw_evidence") != raw["raw_record"]:
                failures.append(f"raw evidence reference mismatch: {trace_id}/{key}")
        timeline_summary = out.get("control_timeline_summary", {})
        required_control_fields = {"format", "raw_evidence", "accessible_fact_ids", "events", "assessment",
                                   "safe_override_available", "override_authorized", "override_duration", "ui_current"}
        if set(timeline_summary) != required_control_fields:
            failures.append(f"unexpected/missing control fields: {trace_id}")
        if out.get("actor_outcome_summary", {}).get("format") != "ACTOR_OUTCOME":
            failures.append(f"actor/outcome summary format invalid: {trace_id}")
        allowed_actor_fields = {"format", "raw_evidence", "accessible_fact_ids", "actor", "agent_action", "effect", "outcome"}
        if set(out.get("actor_outcome_summary", {})) != allowed_actor_fields:
            failures.append(f"unexpected actor/outcome fields: {trace_id}")
        for key in ("safe_override_available", "override_authorized", "override_duration", "ui_current"):
            if timeline_summary.get(key) != raw.get(key):
                failures.append(f"control evidence missing or altered: {trace_id}/{key}")
        if out.get("control_timeline_summary", {}).get("assessment") != recomputed:
            failures.append(f"timeline assessment mismatch: {trace_id}")
        events = out.get("control_timeline_summary", {}).get("events", [])
        if events != independently_reconstruct(raw):
            failures.append(f"timeline reconstruction mismatch: {trace_id}")
    if candidate.get("non_authoritative_negative_controls") != fixture.get("negative_controls"):
        failures.append("negative controls missing or altered")
    if any(control.get("authoritative") is not False or control.get("visible_in_primary_summaries") is not False
           for control in candidate.get("non_authoritative_negative_controls", [])):
        failures.append("non-authoritative negative control promoted into primary evidence")
    summaries = [summary for out in actual_by_id.values() for summary in
                 (out.get("actor_outcome_summary", {}), out.get("control_timeline_summary", {}))]
    if any(control.get("claim") in json.dumps(summaries) for control in fixture.get("negative_controls", [])):
        failures.append("negative-control narrative exposed in a primary summary")
    for out in actual_by_id.values():
        if "blame" in json.dumps(out).lower() or "exculpat" in json.dumps(out).lower():
            failures.append("normative blame/exculpation leaked into primary output")
            break
    return {"status": "PASS_METHOD" if not failures else "FAIL_METHOD", "failures": failures,
            "audited_trace_count": len(raw_by_id)}


if __name__ == "__main__":
    fixture_path, oracle_path, candidate_path = sys.argv[1:4]
    with open(fixture_path, encoding="utf-8") as handle:
        fixture_data = json.load(handle)
    with open(oracle_path, encoding="utf-8") as handle:
        oracle_data = json.load(handle)
    with open(candidate_path, encoding="utf-8") as handle:
        candidate_data = json.load(handle)
    print(json.dumps(audit(fixture_data, oracle_data, candidate_data), sort_keys=True, separators=(",", ":")))
