"""Frozen live-event replay plus missing/conflicting identity controls."""
import hashlib,json
from pathlib import Path
from event_cursor import EventCursor as Baseline
from event_cursor_v2 import EventCursor
HERE=Path(__file__).resolve().parent;out=HERE/'results/event-scope-01';out.mkdir(exist_ok=False)
source=HERE/'results/early-effect-self-use-01/delivered.jsonl';records=list(map(json.loads,source.read_text().splitlines()))
old=Baseline();new=EventCursor()
for r in records:old.append(r);new.append(r)
wrong=old.read_until(0,['terminal'],0);correct=new.read_until(0,['terminal'],0,action_id='confirm_excel')
assert wrong['records'][-1]['id']=='enter_save' and correct['records'][-1]['id']=='confirm_excel'
assert correct['records']==records[:correct['cursor']]
effect=new.read_until(correct['cursor'],['effect_evidence'],0,action_id='confirm_excel')
assert effect['status']=='boundary' and effect['records'][-1]['effect']['action_id']=='confirm_excel'
cases=[('other',{'event':'terminal','id':'other'},'timeout'),
       ('missing',{'event':'terminal'},'identity_unknown'),
       ('conflict',{'event':'effect_evidence','final_program':'target','effect':{'action_id':'other'}},'identity_conflict'),
       ('rejection',{'event':'rejected','reason':'stale observation'},'unattributed_rejection')]
controls=[]
for name,record,expected in cases:
    s=EventCursor();s.append(record);r=s.read_until(0,['terminal','effect_evidence'],0,action_id='target')
    assert r['status']==expected and r['records']==[record];controls.append(dict(case=name,status=r['status']))
try:new.read_until(0,['clock'],0,action_id='target')
except ValueError:pass
else:raise AssertionError('unsupported scoped event')
report=dict(baseline_terminal=wrong['records'][-1]['id'],scoped_terminal=correct['records'][-1]['id'],
            prefix_records=len(correct['records']),effect_cursor=effect['cursor'],controls=controls)
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
paths=[Path(__file__),HERE/'event_scope.py',HERE/'event_cursor_v2.py',source]
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n');print(json.dumps(report,indent=2))
