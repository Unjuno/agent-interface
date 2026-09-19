from __future__ import annotations
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
for p in [
    ROOT/'authority_end_identity_binding_v1',
    ROOT/'authority_ended_validator_byte_binding_v3',
    ROOT/'authority_ended_restart_durability_v1',
]:
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

from authority_end_identity_binding_v1 import bind_authority_end_identity
from validator_byte_pinned_ledger_v3 import BytePinnedValidatorLedger

class BoundAuthorityIssueLedger:
    """Project-facing composition boundary: bind runtime identity before durable issue."""
    def __init__(self,path,*,validator_id,validator_source,function_name='to_caller_execution_decision',initialize=False,fault=None):
        self._inner=BytePinnedValidatorLedger(
            path,
            validator_id=validator_id,
            validator_source=validator_source,
            function_name=function_name,
            initialize=initialize,
            fault=fault,
        )

    @property
    def entries(self):
        return self._inner.entries

    @property
    def validator_sha256(self):
        return self._inner.validator_sha256

    def issue(self,receipt,terminal,*,fault=None):
        bound=bind_authority_end_identity(receipt,terminal)
        return self._inner.issue(bound,fault=fault)

    def recover_pending(self,rid):
        return self._inner.recover_pending(rid)

    def consume(self,token,*,fault=None):
        return self._inner.consume(token,fault=fault)

    def revalidate(self,token,current_sequence,*,association_changed=False):
        return self._inner.revalidate(token,current_sequence,association_changed=association_changed)
