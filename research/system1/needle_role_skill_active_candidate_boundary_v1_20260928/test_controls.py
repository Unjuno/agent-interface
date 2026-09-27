"""Corruption controls for the independent Issue #4986 raw-only auditor."""
import copy, json, subprocess, sys, tempfile
from pathlib import Path

raw=json.loads(Path('/raw/raw.json').read_text())
mutations=[]
for label,change in [
    ('decision',lambda x:x['events'][0].update(decision='REJECTED')),
    ('candidate_bytes',lambda x:x['events'][0].update(candidate_b64='e30=')),
    ('before_digest',lambda x:x['events'][1].update(before_sha256='0'*64)),
    ('rollback',lambda x:x['events'][7].update(after_sha256='f'*64)),
    ('stale_dispatch',lambda x:x['events'][6].update(dispatch_count=1)),
    ('missing_case',lambda x:x['events'].pop()),
]:
    mutant=copy.deepcopy(raw); change(mutant)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.json',delete=False,dir='/tmp') as f:
        json.dump(mutant,f,separators=(',',':')); p=f.name
    out=p+'.audit'
    proc=subprocess.run([sys.executable,'-B','audit.py',p,out],capture_output=True,text=True)
    Path(p).unlink(missing_ok=True); Path(out).unlink(missing_ok=True)
    if proc.returncode==0: raise SystemExit('MUTATION_ACCEPTED:'+label)
    mutations.append(label)
print(json.dumps({'controls':len(mutations),'rejected':mutations},sort_keys=True))

