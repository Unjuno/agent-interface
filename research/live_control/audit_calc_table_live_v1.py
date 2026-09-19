"""Audit actual Calc modal transitions and manual recovery through socket transport."""
import json
from pathlib import Path
from openpyxl import load_workbook
from audit_cause_servo_v2 import frames,read
from decision_receipt_v4 import build as receipt
from input_state_table_v1 import build,decode,selected,canonical
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;root=HERE/'results/calc-table-live-01';runtime=root/'runtime'
for name,sha in read(root/'initial/plan.json')['sources'].items():
    assert digest((HERE/name).read_bytes())==sha
for name,sha in read(runtime/'sources.json').items():
    assert digest((HERE.parent/name).read_bytes())==sha
raw=[json.loads(line) for line in (runtime/'events.jsonl').read_text().splitlines()]
covered=set();exchanges=0
pairs=[(p,p.with_name(p.name.replace('-request','-reply'))) for p in root.glob('*/query-*-request.json')]
pairs.append((root/'decision-request.json',root/'decision-reply.json'))
for qp,rp in pairs:
    q,r=read(qp),read(rp);a,b=q['after'],r['cursor']
    assert b-a==len(r['records']) and r['records']==raw[a:b] and r['status']=='boundary'
    assert not covered.intersection(range(a,b));covered.update(range(a,b));exchanges+=1
    if 'command' in q:
        echo=dict(q['command'],transport_request_id=q['request_id'])
        assert sum(e['event']=='command' and e['command']==echo for e in r['records'])==1
assert covered==set(range(len(raw)))
owners=read(runtime/'owner-events.json');sizes=[];causes=[]
for stage in ('enter','save','inspect','confirm','verify'):
    data=(root/stage/'report.json').read_bytes();report=json.loads(data)
    states=read(root/stage/'state-table.json');review=read(root/stage/'receipt.json')
    assert build(data)==states and receipt(data)==review
    assert canonical(decode(states['table']))==canonical(selected(report))
    assert review['program_binding'] is not None and review['detail_review_required']
    terminal=report['terminal'];release=terminal['release']
    assert release in owners and release['verified'] and not release['buttons_down'] and not release['keys_down']
    if stage in ('save','confirm'):
        assert terminal['status']=='needs_decision' and terminal['decision_reason']=='focus_changed'
        assert terminal['steps_completed']==0
        cause=terminal['interruption'];assert cause['record'] in owners
        assert cause['record']['reason']=='focus_changed' and cause['record']['verified']
        causes.append(cause['intent_token'])
        stage_events=[e for e in raw if e.get('id')==stage and e['event']=='step_started']
        assert len(stage_events)==1 and stage_events[0]['step']==0
    else:
        assert terminal['status']=='completed' and terminal['interruption'] is None and terminal['decision_reason'] is None
    delivered=read(root/stage/'result.json')
    assert delivered['receipt']==review and delivered['state_table']==states
    sizes.append(dict(stage=stage,selected_rows_bytes=len(canonical(selected(report)).encode()),
        full_companion_bytes=len(canonical(states).encode()),observations=len(states['table']['observations'])))
assert len(set(causes))==2
decision=read(root/'gui-decision.json');sha=digest((root/'gui-decision.json').read_bytes())
matches=[(i,e) for i,e in enumerate(raw) if e['event']=='command' and e['command'].get('gui_decision_sha256')==sha]
assert len(matches)==1;index,echo=matches[0]
assert decision['image_sha256']==digest((runtime/'014.png').read_bytes())
assert raw[index+1]['event']=='clock' and raw[index+1]['sequence']==14
assert not any(e['event']=='independent_evaluation' for e in raw[:index+1])
wb=load_workbook(runtime/'sheet.xlsx',data_only=True)
actual=[wb.active['A1'].value,wb.active['A2'].value];wb.close()
assert actual==[816,345] and raw[-1]['success'] and raw[-1]['actual']==actual
observations=frames(runtime,raw)
result=dict(audit_passed=True,audit_sha256=digest(Path(__file__).read_bytes()),events=len(raw),socket_exchanges=exchanges,
    exact_frames=len(observations),selected_state_sizes=sizes,actual=actual,workbook_sha256=digest((runtime/'sheet.xlsx').read_bytes()),
    initial_capture_to_gui_decision_seconds=(echo['received_ns']-observations[0]['capture_ns'])/1e9,
    initial_capture_to_final_evaluation_seconds=(raw[-1]['known_ns']-observations[0]['capture_ns'])/1e9,
    limits='One actual familiar Calc task, natural modal transitions, manual recovery. No controlled A/B or forced fault injection; no model token or speed claim; no independent child-process inventory.')
with (root/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
