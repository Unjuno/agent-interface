from __future__ import annotations
from dataclasses import dataclass, field
from authority_ended_bridge_v1 import to_caller_execution_decision

class DuplicateAuthorityEndedReceipt(ValueError): pass
class InvalidAuthorityEndIdentity(ValueError): pass

@dataclass
class ReplanToken:
    authority_end_id: str
    post_sequence: int
    used: bool = False

@dataclass
class ReplanReceiptLedger:
    issued_ids: set[str] = field(default_factory=set)
    def issue(self, receipt):
        decision=to_caller_execution_decision(receipt)
        if decision != {'status':'safe_yield','reason':'authority_unavailable','completed_actions':receipt['steps_completed']}:
            raise ValueError('unexpected bridge decision')
        rid=receipt.get('authority_end_id')
        if type(rid) is not str or not rid:
            raise InvalidAuthorityEndIdentity('runtime authority_end_id required')
        if rid in self.issued_ids:
            raise DuplicateAuthorityEndedReceipt('authority_end_id already issued')
        self.issued_ids.add(rid)
        return ReplanToken(authority_end_id=rid,post_sequence=receipt['post_authority']['sequence'])

def current_revalidation(token,current_sequence,*,association_changed=False):
    if token.used:return {'status':'token_replay'}
    if type(current_sequence) is not int or current_sequence<=token.post_sequence:return {'status':'stale'}
    if association_changed:return {'status':'association_changed'}
    return {'status':'revalidated'}
def consume_for_execute(token):
    if token.used:raise ValueError('replan token already used')
    token.used=True
