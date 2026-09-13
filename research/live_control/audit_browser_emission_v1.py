"""Audit browser direct completion and skipped optional followup from actual evidence."""
import json
from pathlib import Path
from urllib.parse import parse_qs
from audit_cause_servo_v2 import frames,read
from decision_receipt_v5 import build as receipt
from input_state_table_v1 import build,decode,selected,canonical
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;root=HERE/'results/browser-emission-live-01';runtime=root/'runtime'
for name,sha in read(root/'initial/plan.json')['sources'].items():assert digest((HERE/name).read_bytes())==sha
for name,sha in read(runtime/'sources.json').items():assert digest((HERE.parent/name).read_bytes())==sha
raw=[json.loads(line) for line in (runtime/'events.jsonl').read_text().splitlines()]
pairs=[(p,p.with_name(p.name.replace('-request','-reply'))) for p in root.glob('*/query-*-request.json')]
pairs.append((root/'decision-request.json',root/'decision-reply.json'));covered=set()
for qp,rp in pairs:
    q,r=read(qp),read(rp);a,b=q['after'],r['cursor']
    assert r['status']=='boundary' and r['records']==raw[a:b] and b-a==len(r['records'])
    assert not covered.intersection(range(a,b));covered.update(range(a,b))
    if 'command' in q:
        echo=dict(q['command'],transport_request_id=q['request_id'])
        assert sum(e['event']=='command' and e['command']==echo for e in r['records'])==1
assert covered==set(range(len(raw)))
owners=read(runtime/'owner-events.json');timings=[]
for stage in ('navigate','replace','confirm'):
    data=(root/stage/'report.json').read_bytes();r=json.loads(data)
    review=receipt(data);assert review==read(root/stage/'receipt.json') and review['program_binding'] is not None
    assert review['program_binding']['program_id']==stage and review['program_binding']['recorded_exchanges']==2
    assert r['state']=='terminal_received' and r['terminal']['status']=='completed'
    assert r['terminal']['steps_completed']=={'navigate':4,'replace':5,'confirm':3}[stage] and r['terminal']['interruption'] is None
    assert r['terminal']['release'] in owners and r['terminal']['release']['verified']
    assert len(r['exchanges'])==2 and 'bounded_followup' not in r
    assert not (root/stage/'bounded-request.json').exists()
    table=read(root/stage/'state-table.json');assert build(data)==table
    assert canonical(decode(table['table']))==canonical(selected(r))
    visible=read(root/stage/'result.json');assert visible['receipt']==review and visible['state_table']==table
    assert visible['lifecycle']==r['lifecycle'] and visible['bounded_followup'] is None
    timings.append(dict(stage=stage,outer_preparation_ms=(r['outer_operation']['prepared_ns']-r['outer_operation']['started_ns'])/1e6))
assert not any(e['event']=='input_stopped' for e in raw)
sha=digest((root/'gui-decision.json').read_bytes());decision=read(root/'gui-decision.json')
matches=[(i,e) for i,e in enumerate(raw) if e['event']=='command' and e['command'].get('gui_decision_sha256')==sha]
assert len(matches)==1;index,echo=matches[0]
assert decision['image_sha256']==digest((runtime/'016.png').read_bytes())
assert not any(e['event']=='independent_evaluation' for e in raw[:index+1])
actual=parse_qs((runtime/'submitted.txt').read_text());assert actual=={'value':['t000227']}==raw[-1]['actual'] and raw[-1]['success']
emissions=[]
for stage in ('initial','navigate','replace','confirm','finish'):
    directory=root/stage/'emission'; payload=(directory/'payload.bin').read_bytes(); er=read(directory/'receipt.json')
    assert json.loads(payload)==read(root/stage/'result.json')
    assert digest(payload)==er['payload_sha256'] and len(payload)==er['payload_bytes']==er['accepted_bytes']
    assert er['status']=='locally_flushed'
    assert er['model_received_ns'] is None and er['model_input_tokens'] is None and er['model_cost'] is None
    clocks=[er[k] for k in ('serialization_started_ns','serialization_finished_ns','write_started_ns','write_finished_ns','flush_finished_ns','attempt_finished_ns')]
    assert clocks==sorted(clocks)
    emissions.append(dict(stage=stage,bytes=len(payload),serialization_ms=(clocks[1]-clocks[0])/1e6,write_flush_ms=(clocks[4]-clocks[2])/1e6))
negative=read(root/'negative-gui-decision.json')
assert negative['image_sha256']==digest((runtime/'012.png').read_bytes())
assert read(root/'replace/result.json')['receipt']['task_success'].startswith('unknown')
observed=frames(runtime,raw)
result=dict(audit_passed=True,audit_sha256=digest(Path(__file__).read_bytes()),events=len(raw),exchanges=len(pairs),frames=len(observed),
    emissions=emissions,actual=actual,submitted_sha256=digest((runtime/'submitted.txt').read_bytes()),timings=timings,
    initial_capture_to_gui_decision_seconds=(echo['received_ns']-observed[0]['capture_ns'])/1e9,
    limits='One known confirmation fixture with new seed and measured local emission; no matched speed, token or novel-task generalization claim.')
with (root/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
