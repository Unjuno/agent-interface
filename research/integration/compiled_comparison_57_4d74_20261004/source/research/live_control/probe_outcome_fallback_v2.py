"""Bounded caller controls; injected exchanges are not live transport evidence."""
import hashlib,json
from pathlib import Path
from outcome_fallback_v2 import wait_with_status
HERE=Path(__file__).resolve().parent
out=HERE/'results/outcome-fallback-controls-02';out.mkdir(exist_ok=False);rows=[];query_ids=[]
for case in ('pending','available','wrong_program','wrong_query','status_timeout','exception','batch_limit','false_evaluation'):
    calls=[]
    def exchange(spec):
        calls.append(spec)
        if len(calls)==1:
            return dict(status='batch_limit' if case=='batch_limit' else 'timeout',cursor=7,records=[])
        query_ids.append(spec['request_id'])
        assert spec['after']==7 and spec['command']=={'op':'finalization_status'}
        if case=='exception':raise TimeoutError('injected socket timeout')
        if case=='status_timeout':return dict(status='timeout',cursor=8,records=[])
        outcome=dict(final_program='other' if case=='wrong_program' else 'program',status='finished',
            admission_closed=True,output_flushed=True,evaluation={'success':case!='false_evaluation'})
        record=dict(event='finalization_status',transport_request_id='other' if case=='wrong_query' else spec['request_id'],
            state='pending' if case=='pending' else 'available',outcome=None if case=='pending' else outcome)
        return dict(status='boundary',cursor=9,records=[record])
    result=wait_with_status(exchange,'submit','program',0,timeout=0,status_timeout=0)
    expected={'pending':'pending','available':'evaluated','wrong_program':'needs_reconciliation','wrong_query':'needs_reconciliation',
              'status_timeout':'pending','exception':'transport_or_protocol_error','batch_limit':'pending','false_evaluation':'evaluated'}[case]
    assert result['result']['state']==expected and len(calls)==(1 if case=='batch_limit' else 2)
    assert result['result']['task_success'] is (True if case=='available' else False if case=='false_evaluation' else None)
    assert len(result['transcript'])==len(calls)
    rows.append(dict(case=case,output=result))
assert len(query_ids)==len(set(query_ids))
for program in ('program','other'):
    calls=[]
    def direct(spec):
        calls.append(spec)
        return dict(status='boundary',cursor=1,records=[dict(event='independent_evaluation',final_program=program,success=True,
            admitted_request=dict(transport_request_id='submit',declared_action_id=program))])
    result=wait_with_status(direct,'submit','program',0)
    assert result['result']['state']==('evaluated' if program=='program' else 'needs_reconciliation')
    assert result['result']['task_success'] is (True if program=='program' else None)
    assert len(calls)==1
    rows.append(dict(case='direct_'+program,output=result))
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'outcome_fallback_v2.py',HERE/'outcome_wait.py',HERE/'request_boundary_v2.py')},indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),unique_fresh_query_ids=len(query_ids),passed=True)))
