"""Effective semantic challenges against retained read-only evidence.

Every intact record set passes first. Each challenge changes well-formed JSON;
only a normal AuditError counts as detection. Other exceptions are failures.
"""
import copy,json,sys,hashlib
from pathlib import Path
from audit import audit_correctness,audit_benchmark,AuditError,compact

def apply(rows,label,cases):
    r=rows[0];last=lambda q: next(iter(q['outputs'].values()))[-1]
    if label=='missing_case':rows.pop()
    elif label=='duplicate_identity':rows[-1]['id']=r['id']
    elif label=='wrong_status':last(r)['candidate']['status']='WAIT'
    elif label=='boolean_alias':last(r)['candidate']['input_dispatched']=0
    elif label=='invented_authority':last(r)['candidate']['authority']='dispatch'
    elif label=='missing_partition':r['outputs'].pop(next(iter(r['outputs'])))
    elif label=='boolean_cut':last(r)['end']=False
    elif label=='input_hash':r['input_sha256']='f'*64
    elif label=='input_mutation':r['input_unchanged']=False
    elif label=='negative_visit':last(r)['visited']=-1
    elif label=='poison_healed':
        i=next(i for i,c in enumerate(cases) if c['id']=='e00-FOCUS_KEYMAP');last(rows[i])['candidate']=dict(status='WAIT',shift_down=True,authority='none',input_dispatched=False)
    elif label=='historical_misreport':
        i=next(i for i,c in enumerate(cases) if c['kind']=='retained');last(rows[i])['reference']['status']='UNKNOWN'
    else:raise ValueError(label)

def run(root):
    root=Path(root);cases=json.loads((root/'CASES.json').read_text());raw=root/'formal/stage-0/correctness-0.jsonl'
    rows=[json.loads(x) for x in raw.read_text().splitlines()]
    labels=('missing_case','duplicate_identity','wrong_status','boolean_alias','invented_authority','missing_partition',
            'boolean_cut','input_hash','input_mutation','negative_visit','poison_healed','historical_misreport')
    outcomes=[];original=compact(rows)
    for label in labels:
        audit_correctness(cases,rows)
        changed=copy.deepcopy(rows);apply(changed,label,cases);wire=compact(changed)
        if wire==original:raise RuntimeError('no-op control '+label)
        try:audit_correctness(cases,json.loads(wire))
        except AuditError as e:outcomes.append(dict(label=label,intact_pass=True,changed=True,rejected=True,reason=str(e),mutated_sha256=hashlib.sha256(wire.encode()).hexdigest()))
        else:raise RuntimeError('missed control '+label)
    specs=json.loads((root/'BENCH_PLAN.json').read_text());inputs=json.loads((root/'BENCH_INPUTS.json').read_text())
    b=json.loads((root/'formal/stage-1/bench-0.jsonl').read_text())
    for label in ('clock_reversed','visit_inflation'):
        audit_benchmark(specs[0],inputs['64'],b);changed=copy.deepcopy(b)
        if label=='clock_reversed':changed['arms']['INCREMENTAL']['cpu_after_ns']=changed['arms']['INCREMENTAL']['cpu_before_ns']-1
        else:changed['arms']['INCREMENTAL']['visited']+=1
        wire=compact(changed)
        if wire==compact(b):raise RuntimeError('no-op')
        try:audit_benchmark(specs[0],inputs['64'],json.loads(wire))
        except AuditError as e:outcomes.append(dict(label=label,intact_pass=True,changed=True,rejected=True,reason=str(e),mutated_sha256=hashlib.sha256(wire.encode()).hexdigest()))
        else:raise RuntimeError('missed control '+label)
    return dict(status='PASS_EFFECTIVE_CONTROLS',controls=outcomes,count=len(outcomes),scientific_reruns=0)
if __name__=='__main__':print(json.dumps(run(sys.argv[1]),sort_keys=True,indent=2))