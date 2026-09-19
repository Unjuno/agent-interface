from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class Decision:
    usable: bool
    reason: str
    requires_fresh_authority: bool = True

def validate(capsule: Mapping[str, Any], *, session_id: str, task_id: str, now_epoch: int) -> Decision:
    if not isinstance(capsule, Mapping): return Decision(False, 'malformed')
    for key, expected, reason in (("session_id",session_id,"session_mismatch"),("task_id",task_id,"task_mismatch")):
        if capsule.get(key) != expected: return Decision(False, reason)
    if not capsule.get('capsule_id'): return Decision(False, 'missing_capsule_id')
    if not isinstance(capsule.get('uncertainty'), list): return Decision(False, 'missing_uncertainty')
    if capsule.get('replay_prohibited') is not True: return Decision(False, 'replay_not_prohibited')
    if capsule.get('authority_transfer') is not False: return Decision(False, 'authority_transfer_forbidden')
    if capsule.get('authority_status') != 'REQUIRE_FRESH': return Decision(False, 'fresh_authority_required')
    expiry = capsule.get('expires_at')
    if type(expiry) is not int: return Decision(False, 'missing_expiry')
    if expiry <= now_epoch: return Decision(False, 'expired')
    if capsule.get('contradictory') is True: return Decision(False, 'contradictory')
    if capsule.get('semantic_status') not in {'IN_PROGRESS','PARTIAL','UNKNOWN'}: return Decision(False, 'invalid_semantic_status')
    return Decision(True, 'advisory_context_only')
