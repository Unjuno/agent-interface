"""Archived live reports and adversarial report controls for receipt v5."""
import copy
import json
from pathlib import Path
from decision_receipt_v5 import build
from decision_receipt_v4 import build as old
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;out=HERE/'results/receipt-lifecycle-01';out.mkdir(exist_ok=False)
rows=[];pins={}
for cohort,stages in [('calc-early-live-01',['enter','save','save-followup','confirm','confirm-followup']),
                      ('calc-combined-live-01',['enter','save','confirm'])]:
    for stage in stages:
        path=HERE/'results'/cohort/stage/'report.json';data=path.read_bytes();r=json.loads(data)
        before=old(data);after=build(data);pins[str(path.relative_to(HERE))]=digest(data)
        expected=r['state']=='terminal_received'
        assert (after['program_binding'] is not None)==expected
        assert after['source']==before['source'] and after['terminals']==before['terminals']
        retained=[a for a in before['attention'] if not (expected and a.get('path')==[] and a.get('reason') in
            ('program binding unverified','caller unresolved or reports reason'))]
        assert all(a in after['attention'] for a in retained)
        assert after['detail_review_required'] and after['task_success']==before['task_success']
        (out/f'{cohort}-{stage}.json').write_text(json.dumps(after,indent=2)+'\n')
        rows.append(dict(cohort=cohort,stage=stage,binding_verified=expected,
            attention_before=len(before['attention']),attention_after=len(after['attention'])))
source=json.loads((HERE/'results/calc-combined-live-01/confirm/report.json').read_bytes())
controls=[]
def test(name,mutate,expected=False):
    report=copy.deepcopy(source);mutate(report)
    result=build(json.dumps(report).encode())
    assert (result['program_binding'] is not None)==expected,name
    assert result['detail_review_required']
    controls.append(dict(case=name,binding_verified=result['program_binding'] is not None,attention=result['attention']))
test('hidden followup command',lambda r:r['exchanges'][2]['request'].update(command={'op':'submit'}))
test('followup cursor gap',lambda r:r['exchanges'][2]['request'].update(after=0))
test('wrong action in followup',lambda r:r['exchanges'][2]['request'].update(action_id='other'))
test('read failure retained',lambda r:r['exchanges'][2].update(read_error={'type':'TimeoutError'}))
test('wrong terminal copy',lambda r:r['terminal'].update(id='other'))
test('invented lifecycle terminal',lambda r:r['lifecycle']['terminal'].update(status='completed'))
test('missing source sequence',lambda r:r['source_image'].pop('sequence'))
test('changed submitted steps',lambda r:r['exchanges'][1]['request']['command'].update(steps=[{'op':'key','key':'x'}]))
test('wrong deadline',lambda r:r['exchanges'][1]['request']['command'].update(valid_until_ns=10**20))
test('missing admission',lambda r:r['exchanges'][1]['reply']['records'][1].update(event='unrecognized'))
test('contradictory last reply',lambda r:r['last_reply'].update(cursor=0))
test('unknown nested error preserved',lambda r:r.update(extra={'error':'must remain visible'}),True)
assert any(a['reason']=='nested exception or negative evidence' for a in controls[-1]['attention'])
result=dict(success=True,archived=rows,controls=controls,evidence_sha256=pins,sources={n:digest((HERE/n).read_bytes()) for n in
    ['decision_receipt_v5.py','probe_receipt_lifecycle_v1.py','decision_receipt_v4.py','decision_receipt_v2.py','stopped_client_v1.py']},
    scope='Offline validation against eight archived live reports; no new input, GUI episode, model speed or token measurement')
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(success=True,archived=len(rows),controls=len(controls),verified=sum(r['binding_verified'] for r in rows))))
