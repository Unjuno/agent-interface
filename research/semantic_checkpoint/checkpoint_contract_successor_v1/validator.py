from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class Decision:
    usable: bool
    reason: str
    requires_fresh_authority: bool = True

def validate(c: Mapping[str, Any], *, session_id: str, task_id: str, last_id: int, now: int) -> Decision:
    if not isinstance(c, Mapping): return Decision(False,'malformed')
    if c.get('session_id') != session_id: return Decision(False,'session_mismatch')
    if c.get('task_id') != task_id: return Decision(False,'task_mismatch')
    if type(c.get('checkpoint_id')) is not int or c['checkpoint_id'] <= last_id: return Decision(False,'non_monotonic_id')
    if c.get('status') not in {'CONFIRMED','PROVISIONAL','UNKNOWN'}: return Decision(False,'invalid_status')
    if not isinstance(c.get('evidence_refs'),list) or not c['evidence_refs']: return Decision(False,'missing_evidence')
    if c.get('resume_policy') not in {'REVERIFY_REQUIRED','SAFE_TO_SKIP_DECLARED'}: return Decision(False,'missing_resume_policy')
    if c.get('authority_transfer') is not False: return Decision(False,'authority_transfer_forbidden')
    if c.get('invalidated') is True: return Decision(False,'invalidated')
    if c.get('contradictory') is True: return Decision(False,'contradictory')
    if type(c.get('expires_at')) is not int or c['expires_at'] <= now: return Decision(False,'expired')
    return Decision(True,'advisory_progress_only')
