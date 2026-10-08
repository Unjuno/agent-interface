"""Post-measurement validation of original bytes and copied negative controls."""
import copy, hashlib, json
from pathlib import Path
import audit
p=Path(__file__).resolve().parent
raw=json.loads((p/'formal/raw.json').read_text());plan=json.loads((p/'prereg.json').read_text())
expected=hashlib.sha256((p/'formal/raw.json').read_bytes()).hexdigest()
assert expected=='fb99faceca9715587bba3ec2b11cd2b5dcf8cde3b92c7559a6fd05da1e9b9e6f'
valid=audit.audit(raw,plan,p)
mutations={
 'clock_order':lambda x:x['records'][0]['rows'][0].__setitem__(6,0),
 'due_1ns':lambda x:x['records'][0]['rows'][1].__setitem__(0,x['records'][0]['rows'][1][0]+1),
 'source':lambda x:x['sources'].__setitem__('native.c','0'*64),
 'schedule':lambda x:x['records'][0]['case'].__setitem__('order',999),
 'load_affinity':lambda x:x['records'][1]['load']['after'].__setitem__('affinity',[0]),
 'load_cpu':lambda x:x['records'][1]['load']['after'].__setitem__('ticks',x['records'][1]['load']['before']['ticks']),
 'load_cleanup':lambda x:x['records'][1]['load'].__setitem__('cleaned',False),
 'pixel':lambda x:x['records'][0]['pixels'].__setitem__(next(iter(x['records'][0]['pixels'])),'AAAA'),
 'server_cleanup':lambda x:x['server'].__setitem__('reaped',False),
 'GIL_mode':lambda x:x['environment'].__setitem__('gil',False),
}
rows=[]
for n,fn in mutations.items():
 x=copy.deepcopy(raw);fn(x)
 try:audit.audit(x,plan,p)
 except ValueError as e:rows.append(dict(test=n,rejected=True,reason=str(e)))
 else:raise RuntimeError('accepted '+n)
bad=copy.deepcopy(valid);bad['summary']['decision']='FORGED'
try:audit.verify_report(bad,valid)
except ValueError:rows.append(dict(test='derived_decision',rejected=True))
else:raise RuntimeError('bad summary accepted')
out=dict(real_audit_pass=True,mutation_count=len(rows),mutations=rows,raw_sha256=expected,
         before_after_tests_identical=(p/'tests_before.json').read_bytes()==(p/'tests_after.json').read_bytes())
(p/'validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
