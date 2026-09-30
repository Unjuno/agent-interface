"""Independent trace auditor; recomputes decisions from raw events and policy."""
import json
import sys
from pathlib import Path

POLICIES = {"LOCAL_GATES_ONLY", "STPA_MODEL_ONLY", "STPA_PLUS_FEEDBACK_MONITORS", "FAIL_CLOSED_UNMAPPED"}
SCENARIOS = {"current_pass_acknowledged", "pass_delivery_lost", "stale_prior_pass_acknowledged", "current_reject_delivered", "unmapped_action_path"}


def main():
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "stpa-feedback-constraint-5327-t0-v1": errors.append("schema")
    traces = raw.get("traces", [])
    if len(traces) != 20: errors.append("trace_count")
    seen = set()
    for row in traces:
        p, s = row.get("policy"), row.get("scenario")
        if p not in POLICIES or s not in SCENARIOS: errors.append("unknown_cell"); continue
        if (p, s) in seen: errors.append("duplicate_cell")
        seen.add((p, s))
        events = row.get("events", [])
        if len(events) != 3 or [e.get("event") for e in events] != ["verifier_result", "feedback_delivery", "action_proposed"]:
            errors.append(f"event_order:{p}:{s}"); continue
        verifier, delivery, proposal = events
        source_pass = verifier.get("decision") == "PASS"
        delivered = delivery.get("delivered") is True
        sequence_matches = verifier.get("sequence") == proposal.get("required_sequence")
        acknowledged_current = delivered and delivery.get("sequence") == proposal.get("required_sequence")
        mapped = proposal.get("mapping_present") is True
        if row.get("source_verifier_pass") is not source_pass or row.get("feedback_delivered") is not delivered or row.get("sequence_matches") is not sequence_matches or row.get("mapping_present") is not mapped:
            errors.append(f"fact_mismatch:{p}:{s}")
        if p == "FAIL_CLOSED_UNMAPPED" and not mapped:
            admitted, reason = False, "UNMAPPED"
        elif p == "STPA_PLUS_FEEDBACK_MONITORS" and not acknowledged_current:
            admitted, reason = False, "FEEDBACK_NOT_CURRENTLY_ACKNOWLEDGED"
        else:
            admitted, reason = source_pass, "ADMITTED" if source_pass else "VERIFIER_REJECT"
        hazardous = admitted and (not acknowledged_current or not source_pass or not mapped)
        false_block = s == "current_pass_acknowledged" and not admitted
        if row.get("admitted") is not admitted or row.get("reason") != reason or row.get("hazardous_admission") is not hazardous or row.get("false_block") is not false_block:
            errors.append(f"decision_mismatch:{p}:{s}")
    if len(seen) != 20: errors.append("cell_coverage")
    baseline_unsafe = sum(r.get("hazardous_admission") is True for r in traces if r.get("policy") == "LOCAL_GATES_ONLY")
    monitor_unsafe = sum(
        r.get("hazardous_admission") is True
        for r in traces
        if r.get("policy") == "STPA_PLUS_FEEDBACK_MONITORS"
        and r.get("scenario") in ("pass_delivery_lost", "stale_prior_pass_acknowledged")
    )
    observed = {"local_baseline_unsafe_admissions": baseline_unsafe, "feedback_monitor_unsafe_admissions": monitor_unsafe}
    summary = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    if any(summary.get(k) != v for k, v in observed.items()): errors.append("summary_mismatch")
    print(json.dumps({"status": "PASS_AUDIT" if not errors else "STOP_AUDIT_MISMATCH", "errors": errors, "traces": len(seen), **observed}, sort_keys=True))
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
