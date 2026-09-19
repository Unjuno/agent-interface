"""Identity negatives for request-scoped admitted-result reads."""
import copy,json
from pathlib import Path
from event_cursor_v4 import EventCursor
HERE=Path(__file__).resolve().parent;root=HERE/'results/request-outcome-self-use-01'
records=list(map(json.loads,(root/'delivered.jsonl').read_text().splitlines()))
effect=next(r for r in records if r['event']=='effect_evidence');rows=[]
for case in ('match','other','missing','conflict','matching_rejection','other_rejection'):
    record=copy.deepcopy(effect)
    if case=='other':record['admitted_request']['transport_request_id']='other'
    elif case=='missing':record.pop('admitted_request')
    elif case=='conflict':record['admitted_request']['declared_action_id']='other-action'
    elif case.endswith('rejection'):record=dict(event='rejected',transport_request_id='confirm' if case=='matching_rejection' else 'other')
    cursor=EventCursor();cursor.append(record)
    reply=cursor.read_until(0,['effect_evidence'],0,request_id='confirm')
    expected={'match':'boundary','other':'timeout','missing':'identity_unknown','conflict':'identity_conflict','matching_rejection':'request_rejected','other_rejection':'timeout'}[case]
    assert reply['status']==expected and reply['records']==[record]
    rows.append(dict(case=case,status=reply['status']))
(HERE/'results/request-boundary-controls.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
