"""Retained live-prefix audit and cursor integrity controls."""
import hashlib,json
from pathlib import Path
from event_cursor import EventCursor
HERE=Path(__file__).resolve().parent;root=HERE/'results/live-event-cursor-01';report=[]
for case in ('save','unsaved'):
    d=root/case;reads=json.loads((d/'cursor-reads.json').read_text())
    visible=[json.loads(x) for x in (d/'supervisor-visible.jsonl').read_text().splitlines()]
    collected=[r for batch in reads for r in batch['records']]
    assert collected==visible[:len(collected)]
    early=next(b for b in reads if b['wanted']=='effect_evidence' and b['status']=='boundary')
    final=next(b for b in reads if b['wanted']=='independent_evaluation' and b['status']=='boundary')
    assert early['records'][-1]['event']=='effect_evidence'
    assert not any(r['event']=='independent_evaluation' for r in early['records'])
    assert final['records'][-1]['event']=='independent_evaluation' and final['cursor']>early['cursor']
    assert early['returned_ns']<final['returned_ns']
    report.append(dict(case=case,records=len(collected),early_to_final_return_ms=(final['returned_ns']-early['returned_ns'])/1e6,
                       early_emit_to_return_ms=(early['returned_ns']-early['records'][-1]['emit_started_ns'])/1e6,
                       complete_prefix=True))
s=EventCursor(3);record={'event':'observation','payload':[1]};s.append(record);record['payload'].append(2)
s.append({'event':'interrupt'});s.append({'event':'effect'})
a=s.read_until(0,['effect'],0);assert [r['event'] for r in a['records']]==['observation','interrupt','effect']
assert a['records'][0]['payload']==[1];a['records'][0]['payload'].append(3)
assert s.read_until(0,['effect'],0)['records'][0]['payload']==[1]
b=s.read_until(0,['effect'],0,max_records=1);assert b['status']=='batch_limit' and b['cursor']==1
assert s.read_until(3,['effect'],0)['status']=='timeout'
s.append({'event':'late'});assert s.read_until(0,['effect'],0)['status']=='gap'
s.close();assert s.read_until(3,['effect'],0)['records']==[{'event':'late'}]
assert s.read_until(4,['effect'],0)['status']=='closed'
try:s.append({'event':'forbidden'})
except ValueError:pass
else:raise AssertionError('append after close')
try:s.read_until(5,['effect'],0)
except ValueError:pass
else:raise AssertionError('future cursor')
report.append(dict(controls='immutable copies, replay, interrupt prefix, batch limit, timeout, explicit gap, close drain, future cursor',passed=True))
(HERE/'results/event-cursor-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'cursor-source.json').write_text(json.dumps({'event_cursor.py':hashlib.sha256((HERE/'event_cursor.py').read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(report,indent=2))
