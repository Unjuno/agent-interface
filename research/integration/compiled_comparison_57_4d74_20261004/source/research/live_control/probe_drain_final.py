"""Recorded early/final stream plus missing and conflicting final controls."""
import copy,hashlib,json
from pathlib import Path
from event_cursor_v5 import EventCursor
from outcome_wait import interpret
from drain_final import drain_final
HERE=Path(__file__).resolve().parent;out=HERE/'results/drain-final-01';out.mkdir(exist_ok=False)
source=HERE/'results/prepared-calc-self-use-01/confirm/reply.json'
batch=json.loads(source.read_text());request_id=batch['records'][-1]['admitted_request']['transport_request_id']
early=interpret(batch,request_id);assert early['state']=='effect_observed'
final_source=HERE/'results/prepared-calc-self-use-01/outcome.json'
final=json.loads(final_source.read_text())['result']['evidence'];rows=[]
for case in ('ready','delayed','other_request','missing_identity','wrong_program','exception'):
    cursor=EventCursor()
    for i in range(early['cursor']):cursor.append(dict(event='prefix'))
    record=copy.deepcopy(final)
    if case=='other_request':record['admitted_request']['transport_request_id']='other'
    if case=='missing_identity':record.pop('admitted_request')
    if case=='wrong_program':
        record['final_program']='other';record['admitted_request']['declared_action_id']='other';record['effect']['action_id']='other'
    if case!='delayed':cursor.append(record)
    calls=[]
    def exchange(spec):
        calls.append(spec);assert spec['timeout']==0 and 'command' not in spec
        if case=='exception':raise TimeoutError('injected socket timeout')
        args=dict(spec);args['request_id']=args.pop('read_request_id');return cursor.read_until(**args)
    result=drain_final(exchange,early,request_id,'confirm_excel')
    expected='evaluated' if case=='ready' else 'needs_reconciliation' if case in ('missing_identity','wrong_program') else 'effect_observed'
    assert result['outcome']['state']==expected and len(calls)==1
    assert early==interpret(batch,request_id)
    if case=='delayed':
        cursor.append(final)
        resumed=drain_final(exchange,result['outcome'],request_id,'confirm_excel')
        assert resumed['outcome']['task_success'] is True
    rows.append(dict(case=case,result=result))
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'drain_final.py',HERE/'event_cursor_v5.py',HERE/'outcome_wait.py',source,final_source)},indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),passed=True)))
