"""One zero-server-wait final read after optional early effect evidence."""
import copy
from outcome_wait import interpret,wait_request


def drain_final(exchange,early,request_id,program_id):
    retained=copy.deepcopy(early)
    if retained.get('state')!='effect_observed':return dict(outcome=retained,attempted=False)
    if retained.get('evidence',{}).get('final_program')!=program_id:
        return dict(outcome=dict(state='needs_reconciliation',task_success=None,reason='early_program_mismatch'),early=retained,attempted=False)
    spec=wait_request(request_id,retained['cursor'],final_only=True,timeout=0)
    result=dict(early=retained,attempted=True,request=spec)
    try:
        batch=exchange(spec);result['reply']=batch
        final=interpret(batch,request_id,final_only=True)
        if final['state']=='evaluated':
            if final['evidence'].get('final_program')!=program_id:
                final=dict(state='needs_reconciliation',task_success=None,reason='final_program_mismatch')
            result['outcome']=final
        elif final['state']=='pending':
            retained['cursor']=final['cursor'];retained['continuation']=final['continuation']
            result.update(outcome=retained,drain_state='pending')
        else:result.update(outcome=final,drain_state=final['state'])
    except Exception as exc:
        result.update(outcome=retained,drain_state='transport_or_protocol_error',error=dict(type=type(exc).__name__,message=str(exc)))
    return result
