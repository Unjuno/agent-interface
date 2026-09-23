from __future__ import annotations
import json, tempfile
from pathlib import Path
from audit import audit

ROOT=Path(__file__).resolve().parent
base=json.loads((ROOT/'RESULT.json').read_text())
controls=[]

def check(name, mutate):
    obj=json.loads(json.dumps(base))
    mutate(obj)
    with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:
        json.dump(obj,f); p=f.name
    rejected=bool(audit(p))
    Path(p).unlink(missing_ok=True)
    controls.append({'name':name,'rejected':rejected})

check('flip_n2_plus1_count', lambda o: o['rows'].__setitem__(next(i for i,r in enumerate(o['rows']) if r['attempts']==2 and r['span_ns']==r['boundary_ns']+1), {**next(r for r in o['rows'] if r['attempts']==2 and r['span_ns']==r['boundary_ns']+1), 'exact_failure_phase_count':0}))
check('change_schedule_hash', lambda o: o.__setitem__('schedule_sha256','0'*64))
check('change_invocation_count', lambda o: o['invocation'].__setitem__('formal_invocations',2))
check('drop_row', lambda o: o['rows'].pop())

out={'decision':'PASS_CORRUPTION_CONTROLS' if all(c['rejected'] for c in controls) else 'FAIL_CORRUPTION_CONTROLS','controls':controls}
(ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
if out['decision'].startswith('FAIL_'): raise SystemExit(2)
