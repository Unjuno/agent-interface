"""Independent raw-only audit for construction_01. Does not import runner."""
import hashlib,json,sys,torch
from loader import validate
with open('/out/result.json',encoding='utf-8') as f: r=json.load(f)
with open('/inputs/expected.json',encoding='utf-8') as f: expected=json.load(f)
with open('/inputs/skill.json','rb') as f: package_bytes=f.read()
artifact,digest=validate('/inputs/skill.json',expected)
errors=[]
if r.get('status')!='CONSTRUCTION_COMPLETE': errors.append('status')
if r.get('kind')!='construction-only' or r.get('formal_blocks')!=0 or r.get('optimizer_steps')!=0 or r.get('retry')!=0: errors.append('scope')
if r.get('rows')!=1000: errors.append('rows')
package_sha=hashlib.sha256(package_bytes).hexdigest()
if r.get('package_sha256')!=package_sha or r.get('package_after_sha256')!=package_sha: errors.append('package_integrity')
if not r.get('decisions_equal') or not r.get('logits_exact') or not r.get('predictions_equal'): errors.append('arm_mismatch')
reload_rows=r.get('reload_rows',[]); reuse_rows=r.get('reuse_rows',[])
if len(reload_rows)!=1000 or len(reuse_rows)!=1000: errors.append('raw_row_count')
if reload_rows!=reuse_rows: errors.append('raw_arm_outputs')
if len(r.get('controls',[]))!=4 or any(c.get('outcome')!='YIELD' for c in r.get('controls',[])) or r.get('control_score_calls')!=0: errors.append('controls')
def tensor(role,key): return torch.tensor(artifact['tensors'][role][key],dtype=torch.float32)
def recompute(role,row):
 x=torch.tensor([row],dtype=torch.float32)
 if role=='A':
  h=torch.tanh(torch.nn.functional.linear(x,tensor('A','enc.0.weight'),tensor('A','enc.0.bias')))
  y=torch.nn.functional.linear(h,tensor('A','head.weight'),tensor('A','head.bias'))
 else:
  h=torch.tanh(torch.nn.functional.linear(x,tensor(role,'core.enc.0.weight'),tensor(role,'core.enc.0.bias')))
  y=torch.nn.functional.linear(h,tensor(role,'core.head.weight'),tensor(role,'core.head.bias'))+h@tensor(role,'a')@tensor(role,'b')/2
 return [float(v) for v in y[0].tolist()],int(y.argmax(-1).item())
raw_errors=[]
for i,(got,alt) in enumerate(zip(reload_rows,reuse_rows)):
 role=('A','B','C')[i%3]; row=expected['roles'][role]['inputs'][i//3 % len(expected['roles'][role]['inputs'])]
 logits,pred=recompute(role,row)
 if got.get('role')!=role or got.get('logits')!=logits or got.get('prediction')!=pred: raw_errors.append(i)
 if alt.get('role')!=role or alt.get('logits')!=logits or alt.get('prediction')!=pred: raw_errors.append(i)
if raw_errors: errors.append('independent_recomputation')
out={'status':'AUDIT_PASS_CONSTRUCTION' if not errors else 'AUDIT_FAIL_CONSTRUCTION','errors':errors,'rows':r.get('rows'),'controls_rejected':sum(c.get('outcome')=='YIELD' for c in r.get('controls',[])),'control_score_calls':r.get('control_score_calls'),'independent_recomputation':{'recomputed_rows':len(reload_rows),'mismatches':raw_errors[:20]},'package_sha256':package_sha,'scope':'construction-only; no formal break-even inference'}
with open('/out/audit.json','w',encoding='utf-8') as f: json.dump(out,f,sort_keys=True,indent=2)
print(json.dumps(out,sort_keys=True)); sys.exit(bool(errors))