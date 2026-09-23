"""At most one outcome read and one read-only status command per invocation."""
import uuid
from outcome_wait import wait_request,interpret
from request_boundary_v2 import request_boundary


def wait_with_status(exchange,request_id,program_id,after,*,timeout=1,status_timeout=1,final_only=False):
    if not isinstance(program_id,str) or not 1<=len(program_id)<=128:raise ValueError('program identity required')
    if type(status_timeout) not in (int,float) or not 0<=status_timeout<=30:raise ValueError('status timeout 0..30 required')
    spec=wait_request(request_id,after,timeout=timeout,final_only=final_only)
    transcript=[]
    def send(request):
        # Retain the attempted request even if exchange raises; never retry here.
        entry=dict(request=request);transcript.append(entry)
        reply=exchange(request);entry['reply']=reply;return reply
    try:
        batch=send(spec);result=interpret(batch,request_id,final_only=final_only)
        if result['state']!='pending' or result['reason']!='timeout':
            return dict(result=result,transcript=transcript)
        query_id='status:'+uuid.uuid4().hex
        query=dict(after=result['cursor'],events=['finalization_status'],timeout=status_timeout,
                   command=dict(op='finalization_status'),request_id=query_id,read_request_id=query_id)
        reply=send(query)
        base=dict(cursor=reply.get('cursor',result['cursor']),authority='none',task_success=None,continuation=None)
        records=reply.get('records',[])
        if reply.get('status')!='boundary' or not records:
            state='pending' if reply.get('status')=='timeout' else 'needs_reconciliation'
            status_result=dict(base,state=state,reason='status_'+str(reply.get('status')))
        else:
            record=records[-1]
            if request_boundary(record,['finalization_status'],query_id)!='boundary':
                status_result=dict(base,state='needs_reconciliation',reason='status_identity_mismatch')
            elif record.get('state') in ('pending','not_requested'):
                status_result=dict(base,state='pending' if record['state']=='pending' else 'unresolved',reason=record['state'],evidence=record)
            else:
                outcome=record.get('outcome')
                if record.get('state')!='available' or not isinstance(outcome,dict) or outcome.get('final_program')!=program_id:
                    status_result=dict(base,state='needs_reconciliation',reason='status_program_or_shape_mismatch',evidence=record)
                elif outcome.get('status')=='finalization_error':
                    status_result=dict(base,state='finalization_error',reason=outcome.get('failure_stage'),evidence=record)
                elif (outcome.get('status')=='finished' and outcome.get('admission_closed') is True
                      and outcome.get('output_flushed') is True and isinstance(outcome.get('evaluation'),dict)
                      and type(outcome['evaluation'].get('success')) is bool):
                    status_result=dict(base,state='evaluated',task_success=outcome['evaluation']['success'],evidence=record)
                else:status_result=dict(base,state='needs_reconciliation',reason='invalid_retained_outcome',evidence=record)
        return dict(result=status_result,transcript=transcript)
    except Exception as exc:
        return dict(result=dict(state='transport_or_protocol_error',task_success=None,authority='none',continuation=None,
                    error=dict(type=type(exc).__name__,message=str(exc))),transcript=transcript)
