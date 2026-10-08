"""Synthetic STPA feedback-constraint scenarios; no production code is invoked."""
from itertools import product

POLICIES = (
    "LOCAL_GATES_ONLY",
    "STPA_MODEL_ONLY",
    "STPA_PLUS_FEEDBACK_MONITORS",
    "FAIL_CLOSED_UNMAPPED",
)
SCENARIOS = (
    "current_pass_acknowledged",
    "pass_delivery_lost",
    "stale_prior_pass_acknowledged",
    "current_reject_delivered",
    "unmapped_action_path",
)


def facts(scenario):
    return {
        "current_pass_acknowledged": (True, True, True, True),
        "pass_delivery_lost": (True, False, True, True),
        "stale_prior_pass_acknowledged": (True, True, False, True),
        "current_reject_delivered": (False, True, True, True),
        "unmapped_action_path": (True, True, True, False),
    }[scenario]


def trace(policy, scenario):
    source_pass, delivered, sequence_matches, mapped = facts(scenario)
    required_seq = 8
    produced_seq = 8 if sequence_matches else 7
    events = [
        {"event": "verifier_result", "sequence": produced_seq, "decision": "PASS" if source_pass else "REJECT"},
        {"event": "feedback_delivery", "delivered": delivered, "sequence": produced_seq if delivered else None},
        {"event": "action_proposed", "required_sequence": required_seq, "mapping_present": mapped},
    ]
    local_ok = True  # fixed true by the frozen fixture for mapped action paths
    acknowledged_current = delivered and produced_seq == required_seq
    if policy == "FAIL_CLOSED_UNMAPPED" and not mapped:
        admitted = False
        reason = "UNMAPPED"
    elif policy == "STPA_PLUS_FEEDBACK_MONITORS" and not acknowledged_current:
        admitted = False
        reason = "FEEDBACK_NOT_CURRENTLY_ACKNOWLEDGED"
    else:
        admitted = local_ok and source_pass
        reason = "ADMITTED" if admitted else "VERIFIER_REJECT"
    hazardous = admitted and (not acknowledged_current or not source_pass or not mapped)
    return {
        "policy": policy,
        "scenario": scenario,
        "events": events,
        "local_gates_pass": local_ok,
        "source_verifier_pass": source_pass,
        "feedback_delivered": delivered,
        "sequence_matches": sequence_matches,
        "mapping_present": mapped,
        "admitted": admitted,
        "reason": reason,
        "hazardous_admission": hazardous,
        "false_block": (scenario == "current_pass_acknowledged" and not admitted),
    }


def all_traces():
    return [trace(policy, scenario) for policy, scenario in product(POLICIES, SCENARIOS)]


def summarize(rows):
    local_unsafe = sum(r["hazardous_admission"] for r in rows if r["policy"] == "LOCAL_GATES_ONLY")
    monitored_unsafe = sum(
        r["hazardous_admission"]
        for r in rows
        if r["policy"] == "STPA_PLUS_FEEDBACK_MONITORS"
        and r["scenario"] in ("pass_delivery_lost", "stale_prior_pass_acknowledged")
    )
    current_admits = all(next(r for r in rows if r["policy"] == p and r["scenario"] == "current_pass_acknowledged")["admitted"] for p in POLICIES if p != "FAIL_CLOSED_UNMAPPED")
    monitored_blocks_missing = all(not r["admitted"] for r in rows if r["policy"] == "STPA_PLUS_FEEDBACK_MONITORS" and r["scenario"] in ("pass_delivery_lost", "stale_prior_pass_acknowledged"))
    unmapped_blocks = not next(r for r in rows if r["policy"] == "FAIL_CLOSED_UNMAPPED" and r["scenario"] == "unmapped_action_path")["admitted"]
    reject_blocks = all(not r["admitted"] for r in rows if r["scenario"] == "current_reject_delivered")
    passed = local_unsafe >= 2 and monitored_unsafe == 0 and current_admits and monitored_blocks_missing and unmapped_blocks and reject_blocks
    return {
        "local_baseline_unsafe_admissions": local_unsafe,
        "feedback_monitor_unsafe_admissions": monitored_unsafe,
        "current_pass_preserved": current_admits,
        "missing_or_stale_feedback_blocked": monitored_blocks_missing,
        "unmapped_fail_closed": unmapped_blocks,
        "current_reject_blocked": reject_blocks,
        "status": "PASS_FEEDBACK_CONSTRAINT_SCOPED" if passed else "FAIL_FEEDBACK_CONSTRAINT",
    }
