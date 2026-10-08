"""Explicit checkpoint-matches-then-finish policy; never sends input or retries."""
import json,re
from request_boundary_v4 import request_boundary

def canonical(value):return json.dumps(value,sort_keys=True,allow_nan=False)

def run(exchange,*,after,contract,checkpoint_id,finish_id,finish_on_match,timeout=5):
    if finish_on_match is not True:raise ValueError('explicit finish-on-match policy required')
    if type(after)is not int or after<0:raise ValueError('received cursor required')
    if any(not isinstance(i,str) or not 1<=len(i)<=128 for i in (checkpoint_id,finish_id)) or checkpoint_id==finish_id:
        raise ValueError('two distinct bounded request IDs required')
    if type(timeout) not in (int,float) or not 0<=timeout<=30:raise ValueError('timeout 0..30 required')
    contract=json.loads(canonical(contract))
    if not isinstance(contract,dict) or set(contract)!={'kind','expected'}:raise ValueError('explicit contract required')
    if contract['kind']=='saved_form_value' and isinstance(contract['expected'],str):actual={'value':[contract['expected']]}
    elif contract['kind']=='saved_cells' and isinstance(contract['expected'],dict) and contract['expected']:actual=contract['expected']
    else:raise ValueError('unsupported contract')
    result=dict(state='needs_reconciliation',continuation_allowed=False,task_success=None,finish_attempted=False,authority='none',exchanges=[])
    def call(spec):
        record=dict(request=spec);result['exchanges'].append(record)
        record['reply']=exchange(spec);return record['reply']
    try:
        query=call(dict(after=after,events=['effect_checkpoint'],timeout=timeout,
            command=dict(op='effect_checkpoint',contract=contract),request_id=checkpoint_id,read_request_id=checkpoint_id))
        if query.get('status')!='boundary':
            result['reason']='checkpoint_'+str(query.get('status','missing_status'))
            if query.get('status') in ('timeout','batch_limit'):result['state']='checkpoint_pending'
            return result
        records=query.get('records');cursor=query.get('cursor')
        if not isinstance(records,list) or not records or type(cursor)is not int or cursor!=after+len(records):return result
        record=records[-1]
        if record.get('event')!='effect_checkpoint' or request_boundary(record,{'effect_checkpoint'},checkpoint_id)!='boundary':return result
        if record.get('task_success','missing') is not None or record.get('authority')!='none':return result
        if record.get('status')=='UNKNOWN' and record.get('reason')=='verifier_busy' and 'evidence' not in record:
            result.update(state='needs_decision',reason='verifier_busy',continuation_allowed=True);return result
        evidence=record.get('evidence',{})
        if not isinstance(evidence,dict):return result
        if canonical(evidence.get('contract'))!=canonical(contract):return result
        if evidence.get('observation_closed') is not False or evidence.get('task_success','missing') is not None or evidence.get('authority')!='none':return result
        if evidence.get('status')=='UNKNOWN':
            result.update(state='needs_decision',reason=evidence.get('reason','evidence_unknown'),continuation_allowed=True);return result
        if evidence.get('status')!='VERIFIED':return result
        if canonical(evidence.get('contract'))!=canonical(contract) or canonical(evidence.get('actual'))!=canonical(actual):return result
        if evidence.get('observation_closed') is not False or evidence.get('task_success','missing') is not None:return result
        if record.get('task_success','missing') is not None or evidence.get('authority')!='none':return result
        if not isinstance(evidence.get('artifact_sha256'),str) or not re.fullmatch('[0-9a-f]{64}',evidence['artifact_sha256']):return result
        result['finish_attempted']=True;result['state']='finalization_unresolved'
        final=call(dict(after=cursor,events=['independent_evaluation'],timeout=timeout,
            command=dict(op='finish'),request_id=finish_id,read_request_id=finish_id))
        if final.get('status')!='boundary' or not isinstance(final.get('records'),list) or not final['records']:return result
        if type(final.get('cursor'))is not int or final['cursor']!=cursor+len(final['records']):return result
        score=final['records'][-1]
        if not isinstance(score.get('evaluation_request'),dict):return result
        if score.get('event')!='independent_evaluation' or request_boundary(score,{'independent_evaluation'},finish_id)!='boundary':return result
        if type(score.get('success'))is not bool:return result
        result.update(state='evaluated',task_success=score['success'],evaluation=score)
    except Exception as exc:
        result.update(state='transport_or_protocol_error',error=dict(type=type(exc).__name__,message=str(exc)))
    return result
