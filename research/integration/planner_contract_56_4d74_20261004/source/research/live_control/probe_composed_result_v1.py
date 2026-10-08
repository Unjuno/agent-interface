"""Archived live results plus changed negative evidence and corrupt encodings."""
import copy
import hashlib
import json
from pathlib import Path
from composed_result_v1 import build, decode
from shared_result_v1 import canonical

HERE = Path(__file__).resolve().parent
root = HERE/'results/composed-result-01'
root.mkdir(exist_ok=False)
rows=[]
for cohort, stages in [
    ('browser-emission-live-01', ['navigate','replace','confirm']),
    ('calc-combined-live-01', ['enter','save','confirm']),
    ('calc-early-live-01', ['save','save-followup','confirm','confirm-followup'])]:
    for stage in stages:
        path=HERE/'results'/cohort/stage/'result.json'
        data=path.read_bytes(); value=json.loads(data); packed=build(data)
        assert canonical(decode(packed))==canonical(value)
        (root/(cohort+'-'+stage+'.json')).write_text(canonical(packed),encoding='utf-8')
        rows.append(dict(cohort=cohort,stage=stage,source_sha256=hashlib.sha256(data).hexdigest(),
            original_bytes=len(canonical(value).encode()),packed_bytes=len(canonical(packed).encode()),
            omitted=packed['omitted'],state_row=packed['observation_state_row']))
base=json.loads((HERE/'results/browser-emission-live-01/replace/result.json').read_bytes())
controls=[]
for name in ('different_image','different_terminal','different_state','unknown_negative','duplicate_state_sequence'):
    value=copy.deepcopy(base)
    if name=='different_image': value['image']['status']='unavailable'
    if name=='different_terminal':value['lifecycle']['terminal']['status']='failed'
    if name=='different_state':value['lifecycle']['observation']['input_state_after']['owned_buttons']=[1]
    if name=='unknown_negative':value['lifecycle']['future_error']={'failed':True,'reason':'not classified'}
    if name=='duplicate_state_sequence':
        t=value['state_table']['table'];t['observations'].append(copy.deepcopy(t['observations'][-1]))
    packed=build(canonical(value).encode())
    assert canonical(decode(packed))==canonical(value)
    if name=='different_image':assert 'image' not in packed['omitted']
    if name=='different_terminal':assert 'terminal' not in packed['omitted']
    if name in ('different_state','duplicate_state_sequence'):assert packed['observation_state_row'] is None
    if name=='unknown_negative':assert packed['document']['lifecycle']['future_error']==value['lifecycle']['future_error']
    controls.append(dict(name=name,passed=True))
valid=build(canonical(base).encode());bad_cases=[]
for name in ('source_changed','duplicate_omission','overwrite','wrong_state'):
    bad=copy.deepcopy(valid)
    if name=='source_changed':bad['document']['receipt']['image']['status']='unknown'
    if name=='duplicate_omission':bad['omitted'].append(bad['omitted'][0])
    if name=='overwrite':bad['document']['image']={'status':'unavailable'}
    if name=='wrong_state':bad['observation_state_row']=0
    try:decode(bad)
    except (ValueError,KeyError,IndexError):bad_cases.append(name)
    else:raise AssertionError(name)
report=dict(roundtrip_passed=True,rows=rows,controls=controls,corrupt_rejected=bad_cases,
    sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in
             ['composed_result_v1.py','probe_composed_result_v1.py']},
    limits='Offline JSON value reconstruction and bytes only; no model-token or GUI result.')
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),controls=len(controls),corrupt=len(bad_cases),
    original_bytes=sum(r['original_bytes'] for r in rows),packed_bytes=sum(r['packed_bytes'] for r in rows))))
