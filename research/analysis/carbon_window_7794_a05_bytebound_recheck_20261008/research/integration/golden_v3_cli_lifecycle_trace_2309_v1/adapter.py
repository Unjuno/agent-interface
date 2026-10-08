from __future__ import annotations

STATES = ("SETUP_DOCTOR","MODEL_ATTEMPT","OBSERVATION","GUARDED_DISPATCH","REFUSAL","USEFUL_EFFECT","STALE_INVALIDATION","REPAIR","TERMINAL_RELEASE","CLEANUP_FAILURE")

def execute(row):
    state=row["state"]; value=dict(row["input"])
    if state not in STATES: raise ValueError("UNKNOWN_LIFECYCLE")
    out={"state":state,"authority_granted":False}
    if state=="SETUP_DOCTOR": out.update(status="doctor_pass")
    elif state=="MODEL_ATTEMPT": out.update(status="model_failed", usage_available=bool(value.get("usage_available")))
    elif state=="OBSERVATION": out.update(status="observed")
    elif state=="GUARDED_DISPATCH": out.update(status="returned", program_completed=True, task_success=False)
    elif state=="REFUSAL": out.update(status="refused", program_completed=False)
    elif state=="USEFUL_EFFECT": out.update(status="returned", program_completed=True, task_success=bool(value["task_success"]), partial_effects=[value["effect"]])
    elif state=="STALE_INVALIDATION": out.update(status="invalidated")
    elif state=="REPAIR": out.update(status="repaired", program_completed=True, task_success=False)
    elif state=="TERMINAL_RELEASE": out.update(status="released")
    elif state=="CLEANUP_FAILURE": out.update(status="runtime_failed", program_completed=True, task_success=False, cleanup_error=value["cleanup_error"], execution=value["execution"])
    return out
