"""Independent-auditor corruption controls; all mutations must be rejected."""
import copy,json,subprocess,sys,tempfile
from pathlib import Path
raw=json.loads(Path('/raw/raw.json').read_text(encoding='utf-8'))
mutations=[
 ('missing_query',lambda x:x['arms'][1]['rows'].pop()),
 ('candidate_before_validation',lambda x:x['arms'][1]['rows'][0].update(package_sha256=x['candidate_sha256'],generation=x['candidate_generation'])),
 ('dispatch',lambda x:x['arms'][1]['rows'][0].update(dispatch_count=1)),
 ('torn_digest',lambda x:x['arms'][1]['rows'][40].update(package_sha256='0'*64)),
 ('wrong_receipt',lambda x:x['arms'][1]['rows'][40].update(receipt_at_read='audit:wrong')),
 ('wave_schedule',lambda x:x['arms'][1]['waves'][3].update(barrier_parties=8)),
]
rejected=[]
for name,change in mutations:
 m=copy.deepcopy(raw);change(m)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.json',delete=False,dir='/tmp') as f:json.dump(m,f,separators=(',',':'));p=f.name
 out=p+'.audit';r=subprocess.run([sys.executable,'-B','audit.py',p,out],capture_output=True,text=True)
 Path(p).unlink(missing_ok=True);Path(out).unlink(missing_ok=True)
 if r.returncode==0:raise SystemExit('MUTATION_ACCEPTED:'+name)
 rejected.append(name)
print(json.dumps({'controls':len(rejected),'rejected':rejected},sort_keys=True))
