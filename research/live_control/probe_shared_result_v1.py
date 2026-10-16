"""Exact reconstruction, preservation controls and total serialized size on live results."""
import copy
import json
from pathlib import Path
from shared_result_v1 import build,decode,canonical
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;out=HERE/'results/shared-result-01';out.mkdir(exist_ok=False)
rows=[];pins={}
for cohort,stages in [('browser-combined-live-01',['navigate','submit-form']),
                      ('calc-combined-live-01',['enter','save','confirm']),
                      ('calc-early-live-01',['save','save-followup','confirm','confirm-followup'])]:
    for stage in stages:
        path=HERE/'results'/cohort/stage/'result.json';data=path.read_bytes();original=json.loads(data)
        packed=build(data);decoded=decode(packed)
        assert canonical(original)==canonical(decoded)
        assert decoded['receipt']['attention']==original['receipt']['attention']
        assert decoded['receipt']['task_success']==original['receipt']['task_success']
        pins[str(path.relative_to(HERE))]=digest(data)
        (out/f'{cohort}-{stage}.json').write_text(json.dumps(packed,indent=2)+'\n')
        rows.append(dict(cohort=cohort,stage=stage,original_bytes=len(canonical(original).encode()),
            packed_bytes=len(canonical(packed).encode()),definitions=len(packed['definitions']),references=len(packed['references'])))
large={'unknown':{'error':'x'*300,'verified':False,'owned_buttons':[1],'future_field':[True,1,1.0,None]}}
controls=[]
for name,value in [('repeated negative',{'a':large,'b':large}),
                   ('literal reference-like data',{'a':large,'b':large,'c':{'shared_value':'r1'}}),
                   ('distinct numeric types',[{'n':True,'padding':'p'*300},{'n':1,'padding':'p'*300},{'n':1.0,'padding':'p'*300}]),
                   ('empty',{}),('scalar',None),('array nesting',[large,{'inside':large}])]:
    packed=build(json.dumps(value).encode());assert canonical(decode(packed))==canonical(value)
    controls.append(dict(case=name,roundtrip=True,original_bytes=len(canonical(value).encode()),packed_bytes=len(canonical(packed).encode())))
for data in [b'{"a":1,"a":2}',b'{"a":NaN}']:
    try:build(data)
    except ValueError:pass
    else:raise AssertionError('ambiguous/nonfinite source accepted')
valid=build(json.dumps([large,large]).encode())
for name in ('missing definition','marker mismatch','overlapping paths'):
    bad=copy.deepcopy(valid)
    if name=='missing definition':bad['definitions'].clear()
    elif name=='marker mismatch':bad['document'][0]={'shared_value':'wrong'}
    else:bad['references'].append(copy.deepcopy(bad['references'][0]))
    try:decode(bad)
    except ValueError:pass
    else:raise AssertionError(name)
result=dict(success=True,archived=rows,controls=controls,rejected_sources=2,rejected_corrupt_encodings=3,evidence_sha256=pins,
    sources={n:digest((HERE/n).read_bytes()) for n in ['shared_result_v1.py','probe_shared_result_v1.py']},
    limits='JSON-value equivalence, not byte-format equivalence or token reduction; no model-facing usability trial yet; representation overhead can increase small payloads.')
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(success=True,archived=rows,controls=controls)))
