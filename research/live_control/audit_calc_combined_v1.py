"""Independent artifact consistency audit of the first actual early-return Calc run."""
import json
from pathlib import Path
from openpyxl import load_workbook
from audit_cause_servo_v2 import frames,read
from stopped_client_v1 import PendingAction
from input_state_table_v1 import build,decode,selected,canonical
from decision_receipt_v4 import build as receipt
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;root=HERE/'results/calc-combined-live-01';runtime=root/'runtime'
for name,sha in read(root/'initial/plan.json')['sources'].items():assert digest((HERE/name).read_bytes())==sha
for name,sha in read(runtime/'sources.json').items():assert digest((HERE.parent/name).read_bytes())==sha
raw=[json.loads(s) for s in (runtime/'events.jsonl').read_text().splitlines()]
pairs=[(p,p.with_name(p.name.replace('-request','-reply'))) for p in root.glob('*/query-*-request.json')]
pairs.extend((q,q.with_name('bounded-reply.json')) for q in root.glob('*/bounded-request.json'))
pairs.append((root/'decision-request.json',root/'decision-reply.json'));covered=set()
for qp,rp in pairs:
    q,r=read(qp),read(rp);a,b=q['after'],r['cursor']
    assert r['status']=='boundary' and r['records']==raw[a:b] and b-a==len(r['records'])
    assert not covered.intersection(range(a,b));covered.update(range(a,b))
    if 'command' in q:
        echo=dict(q['command'],transport_request_id=q['request_id'])
        assert sum(e['event']=='command' and e['command']==echo for e in r['records'])==1
assert covered==set(range(len(raw)))
owners=read(runtime/'owner-events.json');metrics=[]
for stage in ('enter','save','confirm'):
    data=(root/stage/'report.json').read_bytes();r=json.loads(data)
    assert receipt(data)==read(root/stage/'receipt.json')
    assert read(root/stage/'receipt.json')['program_binding'] is None  # Known incompatible state name.
    table=read(root/stage/'state-table.json');assert build(data)==table
    assert canonical(decode(table['table']))==canonical(selected(r))
    exchanges=r['exchanges'];q=exchanges[1]['request'];c=q['command'];clock=exchanges[0]['reply']['records'][-1]
    assert c['op']=='submit' and c['expected_sequence']==clock['sequence']==r['source_image']['sequence']
    assert c['valid_until_ns']==clock['runtime_ns']+30_000_000_000
    tracker=PendingAction(c['id'],q['after'])
    for x in exchanges[1:]:tracker.ingest(x['request']['after'],x['reply'])
    assert tracker.view()==r['lifecycle'] and tracker.uncertainty is None
    delivered=read(root/stage/'result.json');assert delivered['lifecycle']==r['lifecycle']
    assert tracker.view()['state']=='terminal_received' and tracker.terminal==r['terminal']
    assert r['terminal']['release'] in owners and r['terminal']['release']['verified']
    if stage in ('save','confirm'):
        initial=read(root/stage/'early-report.json')
        assert initial['state']=='input_stopped_capture_pending'
        assert r['bounded_followup']['server_wait_ms']==400 and r['bounded_followup']['read_error'] is None
        assert r['outer_operation']['started_ns']<=exchanges[0]['started_ns']<exchanges[2]['returned_ns']<=r['outer_operation']['prepared_ns']
        assert exchanges[:2]==initial['exchanges'] and len(exchanges)==3
        assert 'command' not in exchanges[2]['request']
        stop=r['lifecycle']['stopped'];terminal=r['terminal']
        assert stop['interruption']['record'] in owners
        assert terminal['status']=='needs_decision' and terminal['steps_completed']==0
        assert terminal['decision_reason']=='focus_changed'
        assert stop['interruption']==terminal['interruption']
        assert exchanges[1]['returned_ns']<terminal['terminal_ns']
        assert not any(e['event'] in ('input_admission','pointer_admission','step_started') for e in exchanges[2]['reply']['records'])
        metrics.append(dict(action=c['id'],bounded_wait_ms=r['bounded_followup']['attempt_elapsed_ms'],outer_operation_ms=(r['outer_operation']['prepared_ns']-r['outer_operation']['started_ns'])/1e6,submit_to_early_reply_ms=(exchanges[1]['returned_ns']-exchanges[1]['started_ns'])/1e6,
            early_reply_before_runtime_terminal_ms=(terminal['terminal_ns']-exchanges[1]['returned_ns'])/1e6,
            terminal_to_followup_reply_ms=(exchanges[2]['returned_ns']-terminal['terminal_ns'])/1e6,
            early_image_sha256=initial['image']['sha256'],followup_image_sha256=r['image']['sha256']))
decision=read(root/'gui-decision.json');sha=digest((root/'gui-decision.json').read_bytes())
matches=[(i,e) for i,e in enumerate(raw) if e['event']=='command' and e['command'].get('gui_decision_sha256')==sha]
assert len(matches)==1;index,echo=matches[0]
assert decision['image_sha256']==digest((runtime/'014.png').read_bytes())
assert not any(e['event']=='independent_evaluation' for e in raw[:index+1])
wb=load_workbook(runtime/'sheet.xlsx',data_only=True);actual=[wb.active['A1'].value,wb.active['A2'].value];wb.close()
assert actual==[816,345] and raw[-1]['success'] and raw[-1]['actual']==actual
observed=frames(runtime,raw)
result=dict(audit_passed=True,audit_sha256=digest(Path(__file__).read_bytes()),events=len(raw),exchanges=len(pairs),frames=len(observed),
    actual=actual,metrics=metrics,initial_capture_to_gui_decision_seconds=(echo['received_ns']-observed[0]['capture_ns'])/1e9,
    workbook_sha256=digest((runtime/'sheet.xlsx').read_bytes()),
    limits='One familiar live task. Receipt v4 binding is unverified for new state names; this audit separately checks actual commands, history and lifecycle. No causal speed or model-token claim.')
with (root/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
