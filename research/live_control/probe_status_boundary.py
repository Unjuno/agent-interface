"""Status query identity controls on candidate EventCursor v5."""
import hashlib,json
from pathlib import Path
from event_cursor_v5 import EventCursor
HERE=Path(__file__).resolve().parent
out=HERE/'results/status-boundary-01';out.mkdir(exist_ok=False);rows=[]
for case,identity,expected in (('matching','query','boundary'),('different','other','timeout'),('missing',None,'identity_unknown')):
    cursor=EventCursor()
    record=dict(event='finalization_status',state='pending',outcome=None)
    if identity is not None:record['transport_request_id']=identity
    cursor.append(record)
    result=cursor.read_until(0,['finalization_status'],timeout=0,request_id='query')
    assert result['status']==expected and result['records']==[record]
    rows.append(dict(case=case,result=result))
cursor=EventCursor()
cursor.append(dict(event='finalization_status',transport_request_id='other',state='available',outcome={'final_program':'other'}))
cursor.append(dict(event='finalization_status',transport_request_id='query',state='pending',outcome=None))
result=cursor.read_until(0,['finalization_status'],timeout=0,request_id='query')
assert result['status']=='boundary' and len(result['records'])==2 and result['records'][-1]['state']=='pending'
rows.append(dict(case='other_snapshot_retained_until_matching_pending',result=result))
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py')},indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),passed=True)))
