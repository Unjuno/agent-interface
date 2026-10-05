"""Recorded cross-app outcomes plus delayed/negative cursor controls."""
import copy,hashlib,json
from pathlib import Path
from event_cursor_v4 import EventCursor
from outcome_wait import interpret,wait_request
HERE=Path(__file__).resolve().parent
out=HERE/'results/outcome-wait-01';out.mkdir(exist_ok=False)
rows=[];sources={}
def read(cursor,after,request,final_only=False):
    spec=wait_request(request,after,final_only=final_only,timeout=0)
    spec['request_id']=spec.pop('read_request_id')
    batch=cursor.read_until(**spec)
    return batch,interpret(batch,request,final_only=final_only)

for cohort,request in (('receipt-image-self-use-01','confirm'),('receipt-browser-self-use-01','submit')):
    source=HERE/'results'/cohort/'delivered.jsonl'
    records=[json.loads(line) for line in source.read_text().splitlines()]
    sources[str(source.relative_to(HERE))]=hashlib.sha256(source.read_bytes()).hexdigest()
    cursor=EventCursor()
    for record in records:cursor.append(record)
    batch,result=read(cursor,0,request)
    assert result['state']==('effect_observed' if request=='confirm' else 'evaluated')
    if request=='confirm':
        assert result['task_success'] is None
        final,scored=read(cursor,batch['cursor'],request,True)
        assert scored['task_success'] is True
        assert batch['records']+final['records']==records[:final['cursor']]
    else:assert result['task_success'] is True
    rows.append(dict(case=cohort,result=result))

template=copy.deepcopy(next(r for r in records if r['event']=='independent_evaluation'))
cursor=EventCursor();cursor.append(dict(event='terminal',id='submit_form',status='completed',
    admitted_request=template['admitted_request']))
batch,pending=read(cursor,0,'submit')
assert pending['state']=='pending' and pending['task_success'] is None and batch['cursor']==1
rows.append(dict(case='completed_input_is_not_task_success',result=pending))
cursor.append(template)
batch,result=read(cursor,pending['cursor'],'submit')
assert result['state']=='evaluated' and result['task_success'] is True
assert len(batch['records'])==1
rows.append(dict(case='delayed_evaluation_resume_without_command',result=result))

for case in ('failed_evaluation','invalid_evaluation','different_request','missing_identity','rejected','closed','gap','unknown_effect'):
    cursor=EventCursor(capacity=1 if case=='gap' else 256)
    record=copy.deepcopy(template)
    if case=='failed_evaluation':record['success']=False
    elif case=='invalid_evaluation':record['success']='true'
    elif case=='different_request':record['admitted_request']['transport_request_id']='other'
    elif case=='missing_identity':record.pop('admitted_request')
    elif case=='rejected':record=dict(event='rejected',transport_request_id='submit')
    elif case=='unknown_effect':
        record.pop('success');record['event']='effect_evidence'
        record['effect']=dict(action_id='submit_form',status='UNKNOWN')
    if case=='gap':cursor.append(dict(event='clock'))
    if case=='closed':cursor.close()
    else:cursor.append(record)
    _,result=read(cursor,0,'submit')
    expected={'failed_evaluation':'evaluated','different_request':'pending','closed':'unresolved',
              'unknown_effect':'effect_observed'}.get(case,'needs_reconciliation')
    assert result['state']==expected,(case,result)
    assert result['task_success'] is (False if case=='failed_evaluation' else None)
    if case=='unknown_effect':assert result['continuation']['events']==['independent_evaluation']
    rows.append(dict(case=case,result=result))

for source in (Path(__file__),HERE/'outcome_wait.py',HERE/'event_cursor_v4.py',HERE/'request_boundary.py'):
    sources[str(source.relative_to(HERE))]=hashlib.sha256(source.read_bytes()).hexdigest()
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),states=[dict(case=r['case'],state=r['result']['state']) for r in rows]),indent=2))
