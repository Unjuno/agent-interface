import json
from hashlib import sha256

CASES = [
    ("READY_FENCE_VALID", "proceed_observe", "ready is admission evidence only"),
    ("READY_FENCE_STALE", "query_readiness", "later initialization invalidates the generation"),
    ("ENDPOINT_BEFORE_READY", "wait", "endpoint visibility is not readiness"),
    ("CLOCK_READ_SUCCEEDS_TASK_EFFECT_UNKNOWN", "proceed_observe", "clock success is not task success"),
    ("READY_EVIDENCE_LOST_OR_DUPLICATED", "query_readiness", "delivery uncertainty is fail-closed"),
    ("HELD_OUT_SECOND_RUNTIME", "query_readiness", "transfer requires independent runtime evidence"),
]
result = {
    "schema": "stale-runtime-readiness-preflight-v1",
    "source_issue": 2224,
    "mode": "container_contract_only",
    "controls": CASES,
    "executed": False,
    "status": "STOP_LIVE_READINESS_TASK_RECOVERY_NOT_EXECUTED",
    "stop_reason": "No connected second runtime/application, model policy, task-input route, or independent effect scorer was available.",
    "authority_boundary": "Readiness, observation, input authority, and task effect are distinct receipts; ready or clock evidence grants neither task success nor input authority.",
    "required_next_evidence": ["stale-generation runtime fixture", "held-out application route", "model startup decisions", "task/effect scoring", "loss/duplication delivery cases"],
}
blob = json.dumps(result, indent=2, sort_keys=True).encode()
print(json.dumps(result, indent=2, sort_keys=True))
print("sha256", sha256(blob).hexdigest())
