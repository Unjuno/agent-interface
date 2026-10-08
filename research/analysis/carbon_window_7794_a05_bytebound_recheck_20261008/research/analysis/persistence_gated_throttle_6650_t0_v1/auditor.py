"""Independent raw-only accounting audit for the 6650 synthetic fixture."""
from __future__ import annotations


def audit(fixture: dict, raw: dict) -> list[str]:
    errors: list[str] = []
    if set(raw.get("traces", {})) != {t["id"] for t in fixture["traces"]}:
        errors.append("trace set mismatch")
        return errors
    for trace in fixture["traces"]:
        tid = trace["id"]
        policies = raw["traces"][tid]
        if set(policies) != {"fixed", "queue_length", "persistence", "oracle"}:
            errors.append(f"{tid}: policy set mismatch")
            continue
        offered = {e["id"]: e for e in trace["events"]}
        for policy, result in policies.items():
            reqs = result.get("requests", [])
            ids = [r.get("id") for r in reqs]
            if len(ids) != len(set(ids)) or set(ids) != set(offered):
                errors.append(f"{tid}/{policy}: offered ID coverage mismatch")
            req_by_id = {r.get("id"): r for r in reqs}
            for oid, event in offered.items():
                row = req_by_id.get(oid)
                if row is None:
                    continue
                if row.get("trace_id") != tid or row.get("offered") is not True:
                    errors.append(f"{tid}/{policy}/{oid}: offered provenance mismatch")
                should_mandatory = event["kind"] == "mandatory"
                if should_mandatory and row.get("status") != "EMITTED":
                    errors.append(f"{tid}/{policy}/{oid}: mandatory request suppressed")
                if row.get("status") == "SUPPRESSED":
                    if not (event["kind"] == "optional" and event["optional_known"] is True
                            and event["session"] is not None and policy in {"persistence", "queue_length", "oracle"}):
                        errors.append(f"{tid}/{policy}/{oid}: ineligible suppression")
                    if not row.get("suppression_receipt"):
                        errors.append(f"{tid}/{policy}/{oid}: missing suppression receipt")
                elif row.get("status") != "EMITTED" or row.get("suppression_receipt") is not None:
                    errors.append(f"{tid}/{policy}/{oid}: malformed emission/suppression")
                if event["kind"] == "optional" and (event["optional_known"] is not True or event["session"] is None):
                    if row.get("status") != "EMITTED" or row.get("control_status") != "UNKNOWN_SCOPE_OR_OPTIONALITY":
                        errors.append(f"{tid}/{policy}/{oid}: unknown optionality failed open")
                if event["kind"] == "optional" and trace["feedback_delay"] > 1:
                    if row.get("status") != "EMITTED" or row.get("control_status") != "UNKNOWN_FEEDBACK":
                        errors.append(f"{tid}/{policy}/{oid}: stale feedback failed open")

            suppressed = {r["id"] for r in reqs if r.get("status") == "SUPPRESSED"}
            serviced = result.get("services", [])
            service_ids = [s.get("id") for s in serviced]
            if len(service_ids) != len(set(service_ids)) or set(service_ids) != set(offered) - suppressed:
                errors.append(f"{tid}/{policy}: service coverage mismatch")
            svc_by_id = {s.get("id"): s for s in serviced}
            for oid, row in svc_by_id.items():
                event = offered.get(oid)
                if event is None:
                    continue
                start = row.get("started_at")
                completed = row.get("completed_at")
                if not isinstance(start, int) or not isinstance(completed, int) or completed != start + event["service"]:
                    errors.append(f"{tid}/{policy}/{oid}: service interval mismatch")
                req = req_by_id.get(oid, {})
                if row.get("enqueued_at") != req.get("offered_at") or row.get("queue_sojourn") != start - req.get("offered_at", start):
                    errors.append(f"{tid}/{policy}/{oid}: enqueue/sojourn provenance mismatch")
                if row.get("generation") != event["generation"] or row.get("optional_known") != event["optional_known"]:
                    errors.append(f"{tid}/{policy}/{oid}: service source metadata mismatch")
                gen_at_start = max((g["generation"] for g in trace["generation_changes"]
                                    if g["session"] == event["session"] and g["t"] <= start), default=0)
                if row.get("generation_at_start") != gen_at_start:
                    errors.append(f"{tid}/{policy}/{oid}: generation-at-start mismatch")
                if row.get("outcome") == "STALE_GENERATION":
                    if event["generation"] == gen_at_start:
                        errors.append(f"{tid}/{policy}/{oid}: false stale-generation label")
                elif row.get("outcome") == "STALE_AT_SERVICE_START":
                    if event["generation"] != gen_at_start or event["deadline"] is None or start <= event["deadline"]:
                        errors.append(f"{tid}/{policy}/{oid}: false stale-at-start label")
                elif row.get("outcome") == "SERVICED_WITHIN_FRESHNESS":
                    if event["generation"] != gen_at_start or (event["deadline"] is not None and start > event["deadline"]):
                        errors.append(f"{tid}/{policy}/{oid}: false fresh label")
                else:
                    errors.append(f"{tid}/{policy}/{oid}: unknown terminal outcome")

            mandatory = {e["id"] for e in trace["events"] if e["kind"] == "mandatory"}
            got_mandatory = {s["id"] for s in serviced if offered[s["id"]]["kind"] == "mandatory"}
            if got_mandatory != mandatory:
                errors.append(f"{tid}/{policy}: mandatory terminal coverage mismatch")
            for s in result.get("states", []):
                if s.get("session") not in {e["session"] for e in trace["events"]}:
                    errors.append(f"{tid}/{policy}: state leaked across session")
                if s.get("oldest_pending_age", -1) < 0 or s.get("eligible_pending", -1) < 0:
                    errors.append(f"{tid}/{policy}: negative queue metric")
    return errors
