"""Read-only completion policy for request-scoped outcome batches.

Early effect evidence is optional. Final evaluation remains a separate outcome.
No command replay, admission, or background polling is performed here.
"""
from request_boundary import request_boundary


def wait_request(request_id,after,*,final_only=False,timeout=5):
    if not isinstance(request_id,str) or not 1<=len(request_id)<=128:
        raise ValueError('bounded request identity required')
    if type(after)is not int or after<0:raise ValueError('nonnegative cursor required')
    if type(final_only)is not bool:raise ValueError('boolean final_only required')
    if type(timeout) not in (int,float) or not 0<=timeout<=30:raise ValueError('timeout 0..30 required')
    return dict(after=after,events=['independent_evaluation'] if final_only else
                ['effect_evidence','independent_evaluation'],timeout=timeout,read_request_id=request_id)


def interpret(batch,request_id,*,final_only=False):
    """Return evidence state and a continuation; never turn silence into failure."""
    if not isinstance(batch,dict):raise ValueError('batch required')
    cursor=batch.get('cursor');records=batch.get('records')
    if type(cursor)is not int or cursor<0 or not isinstance(records,list):raise ValueError('invalid batch')
    continuation=wait_request(request_id,cursor,final_only=final_only)
    status=batch.get('status')
    base=dict(cursor=cursor,authority='none',task_success=None)
    if status in ('gap','identity_unknown','identity_conflict','request_rejected'):
        return dict(base,state='needs_reconciliation',reason=status,continuation=None)
    if status in ('timeout','batch_limit'):
        return dict(base,state='pending',reason=status,continuation=continuation)
    if status=='closed':
        return dict(base,state='unresolved',reason='stream_closed_without_requested_outcome',continuation=None)
    if status!='boundary' or not records:
        return dict(base,state='unresolved',reason='unexpected_transport_result',continuation=None)
    record=records[-1]
    events=continuation['events']
    if request_boundary(record,events,request_id)!='boundary':
        return dict(base,state='needs_reconciliation',reason='outcome_identity_or_type_mismatch',continuation=None)
    if record['event']=='independent_evaluation':
        if type(record.get('success'))is not bool:
            return dict(base,state='needs_reconciliation',reason='invalid_evaluation',continuation=None)
        return dict(base,state='evaluated',task_success=record['success'],evidence=record,continuation=None)
    effect=record.get('effect')
    if not isinstance(effect,dict) or effect.get('status') not in ('VERIFIED','CONTRADICTED','UNKNOWN'):
        return dict(base,state='needs_reconciliation',reason='invalid_effect',continuation=None)
    return dict(base,state='effect_observed',effect_status=effect['status'],evidence=record,
                continuation=wait_request(request_id,cursor,final_only=True))
