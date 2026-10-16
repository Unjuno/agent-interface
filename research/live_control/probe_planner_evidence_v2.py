"""Strict-contract controls and valid-output equivalence for compact evidence."""
import copy,hashlib,json
from pathlib import Path
import planner_evidence_v1 as measured
import planner_evidence_v2 as candidate
H=Path(__file__).resolve().parent;R=H/'results/planner-evidence-controls-02';R.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
form=H/'results/checkpoint-recovery-form-01';calc=H/'results/checkpoint-decision-calc-01'
fl=read(form/'losses.json');ct=read(calc/'turns.json')
specs=[('form_unknown',fl[0]['recovered']['state']['last_resolution'],None,None,True),
       ('form_verified',fl[1]['recovered']['state']['last_resolution'],None,None,True),
       ('calc_unknown',ct[1]['feedback']['checkpoint_resolution'],ct[0]['phases'],ct[0]['proposal']['steps'],False),
       ('calc_verified',ct[1]['checkpoint']['state']['last_resolution'],None,None,False)]
equivalent=[]
for name,resolution,phase,steps,recovered in specs:
 a=measured.present(resolution,phase_report=phase,prior_steps=steps,recovered=recovered)
 b=candidate.present(resolution,phase_report=phase,prior_steps=steps,recovered=recovered)
 assert a==b and json.dumps(a,separators=(',',':'))==json.dumps(b,separators=(',',':'))
 equivalent.append(name)
base=fl[0]['recovered']['state']['last_resolution'];refused=[]
mutations=[]
wrong=copy.deepcopy(base);wrong['checkpoint']['evidence'].pop('contract');mutations.append(('missing_contract',wrong))
wrong=copy.deepcopy(base);wrong['checkpoint']['evidence']['contract']={'kind':'saved_form_value'};mutations.append(('malformed_contract',wrong))
wrong=copy.deepcopy(base);wrong['checkpoint']['evidence']['contract']={'kind':'unknown','expected':'t000240'};mutations.append(('unsupported_contract',wrong))
wrong=copy.deepcopy(base);wrong['checkpoint']['evidence']['contract']={'kind':'saved_form_value','expected':'x'*1025};mutations.append(('oversized_contract',wrong))
for name,value in mutations:
 try:candidate.checkpoint(value)
 except ValueError:refused.append(name)
 else:raise AssertionError(name)
assert len(refused)==4
sources=[Path(__file__),H/'planner_evidence_v1.py',H/'planner_evidence_v2.py',H/'checkpoint_contract_v1.py',form/'losses.json',calc/'turns.json']
report={'scope':'offline validation of archived live evidence; no model calls or input',
        'valid_views_byte_equivalent_to_measured_v1':equivalent,
        'additional_contract_refusals':refused,
        'measured_v1_status':'frozen experiment source; do not promote',
        'candidate':'planner_evidence_v2.py',
        'sources':{str(p.relative_to(H)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(R/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
