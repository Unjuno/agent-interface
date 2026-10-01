"""Independent whole-history oracle for Issue #1616."""
from collections import Counter
from model import EVENTS

BAD = {"RELEASE_BAD_TOKEN", "EFFECT_BAD_TOKEN", "EFFECT_AUTH", "TERMINAL_BAD_TOKEN"}


def oracle(trace):
    counts = Counter(trace)
    reasons = []
    if any(x not in EVENTS for x in trace): reasons.append("unknown_event")
    if any(counts[x] for x in BAD): reasons.append("invalid_lineage_or_authority")
    for x in ("RELEASE_OK","EFFECT_OK","TIMEOUT","TERMINAL_OK"):
        if counts[x] > 1: reasons.append("duplicate:"+x)
    if counts["EFFECT_OK"] and counts["TIMEOUT"]:
        reasons.append("effect_timeout_conflict")
    uncertain = bool(reasons)
    released = counts["RELEASE_OK"] == 1
    effect = counts["EFFECT_OK"] == 1
    timeout = counts["TIMEOUT"] == 1
    terminal = counts["TERMINAL_OK"] == 1
    if uncertain:
        effect_status = "unknown"
    elif effect:
        effect_status = "resolved"
    elif timeout:
        effect_status = "unresolved"
    else:
        effect_status = "pending"
    return {
        "state":"needs_reconciliation" if uncertain else "tracked",
        "physical_release_verified":released and not uncertain,
        "client_can_resume_reasoning":released and not uncertain,
        "task_effect_status":effect_status,
        "task_effect_resolved":effect and not uncertain,
        "effect_timeout_recorded":timeout and not uncertain,
        "terminal_received":terminal and not uncertain,
        "program_terminal_pending":not terminal and not uncertain,
        "current_input_authority":False,
        "new_input_admissible":False,
        "semantic_authority":False,
        "uncertainty_class": None if not uncertain else "invalid",
    }


def normalize_candidate(view):
    out=dict(view)
    out["uncertainty_class"] = None if view["uncertainty"] is None else "invalid"
    out.pop("uncertainty",None)
    return out
