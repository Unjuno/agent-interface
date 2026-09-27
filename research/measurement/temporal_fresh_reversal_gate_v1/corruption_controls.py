from __future__ import annotations
import json,subprocess,sys,tempfile
src=json.load(open('RESULT.json'))
mutations=[('decision','FAIL_FRESH_REVERSAL_GATE'),('random_reversal_continue_escapes',1),('authority_grants',1),('random_digest_sha256','0'*64)]
rows=[]
for name,val in mutations:
    d=dict(src); d[name]=val
    with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f: json.dump(d,f); p=f.name
    q=subprocess.run([sys.executable,'audit.py',p],capture_output=True,text=True)
    rows.append({'mutation':name,'rejected':q.returncode!=0})
out={'all_rejected':all(x['rejected'] for x in rows),'controls':rows}
open('MUTATION_CONTROLS.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['all_rejected'] else 1)
