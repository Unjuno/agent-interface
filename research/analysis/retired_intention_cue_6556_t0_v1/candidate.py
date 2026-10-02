"""Finite policy comparator for Issue #6556; no runtime or GUI access."""
import json
import sys
from pathlib import Path


def decide(case, policy):
    current, event = case["current"], case["event"]
    active = current["active"] and current["intent"] is not None
    cue_matches = active and event["cue"] == current["cue"]
    decision = "REFUSE"
    lineage = None
    reason = "inactive_or_cue_mismatch"
    if policy in ("CUE_ONLY", "UNSUBSCRIBE_ONLY"):
        if cue_matches:
            decision, lineage, reason = "ADMIT", current["instance"], "matching_cue_on_active_listener"
    elif policy == "CURRENT_GENERATION_AT_DELIVERY":
        if cue_matches and event["delivery_listener"] == current["instance"]:
            decision, lineage, reason = "ADMIT", current["instance"], "bound_to_generation_active_at_delivery"
    elif policy == "DURABLE_INSTANCE_EVENT_ID":
        if cue_matches and event["target_instance"] == current["instance"] and event["id"] not in case["seen_event_ids"]:
            decision, lineage, reason = "ADMIT", current["instance"], "instance_target_matches_and_id_unseen"
        else:
            reason = "instance_target_mismatch_or_duplicate"
    elif policy == "ORIGIN_GENERATION_RETIREMENT_FENCE":
        origin = event["origin"]
        if origin is None:
            decision, reason = "UNKNOWN", "origin_identity_missing"
        elif origin["instance"] in case["retired_instances"]:
            decision, reason = "REFUSE", "origin_instance_retired"
        elif cue_matches and origin == {"intent": current["intent"], "generation": current["generation"], "instance": current["instance"]} and event["id"] not in case["seen_event_ids"]:
            decision, lineage, reason = "ADMIT", origin["instance"], "active_origin_identity_matches"
        else:
            reason = "origin_generation_mismatch_or_duplicate"
    else:
        raise ValueError(f"unknown policy: {policy}")
    return {
        "case_id": case["id"], "policy": policy, "decision": decision,
        "response_lineage": lineage, "reason": reason,
        "obligation_status": case["obligation"],
        "effect_resolved": False, "release_resolved": False
    }


def run(fixture):
    return {"schema": "issue-6556-t0-candidate-v1", "rows": [
        decide(case, policy) for case in fixture["cases"] for policy in fixture["policies"]
    ]}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json OUTPUT.json")
    fixture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    Path(argv[2]).write_text(json.dumps(run(fixture), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
