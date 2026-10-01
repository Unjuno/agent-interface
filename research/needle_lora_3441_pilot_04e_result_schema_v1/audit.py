"""Independent CPU audit for the retained fresh-seed multi-skill result."""
import base64,hashlib,io,json,sys,torch
SEED=5920
def dataset(n,seed,flip0=False,flip1=False):
 g=torch.Generator(device="cpu").manual_seed(seed)
 x=torch.randn((n,8),generator=g,dtype=torch.float32)
 b0=(x[:,0]>0).long();b1=(x[:,1]>0).long()
 if flip0:b0=1-b0
 if flip1:b1=1-b1
 y=b0*2+b1
 return x,y,hashlib.sha256(x.numpy().tobytes()+y.numpy().tobytes()).hexdigest()
r=json.load(open(sys.argv[1],encoding="utf-8"))
errors=[]
if r.get("parameters",{}).get("seed")!=SEED:errors.append("seed")
if r.get("allocation")!="needle-lora-3441-pilot-04e-result-schema-20260926-01":errors.append("allocation")
if r.get("parameters",{}).get("base_pretrain_steps")!=400:errors.append("base_pretrain_steps")
if r.get("parameters",{}).get("adapter_steps_per_fit")!=120:errors.append("adapter_steps_per_fit")
specs={"A":(4096,SEED+4,False,False),"B":(4096,SEED+5,True,False),"C":(4096,SEED+6,False,True)}
stored=r.get("measurements",{}).get("row_evidence",{})
for arm in ("routed","shared"):
 rows=stored.get(arm,{})
 if set(rows)!=set(specs):errors.append(arm+":skills");continue
 for skill,(n,ds,f0,f1) in specs.items():
  x,y,digest=dataset(n,ds,f0,f1);row=rows[skill]
  exp=row.get("expected");pred=row.get("predicted")
  if r.get("data_sha256",{}).get(skill+"_eval")!=digest:errors.append(skill+":data_hash")
  if exp!=y.tolist():errors.append(skill+":"+arm+":expected_rows")
  if not isinstance(pred,list) or len(pred)!=n or any(type(v)is not int or v not in range(4) for v in pred):
   errors.append(skill+":"+arm+":prediction_rows");continue
  correct=sum(int(a==b) for a,b in zip(exp,pred))
  if row.get("n")!=n or row.get("correct")!=correct or row.get("accuracy")!=correct/n:errors.append(skill+":"+arm+":metric")
  declared=r.get("measurements",{}).get("routed_accuracy" if arm=="routed" else "shared_sequential_accuracy",{}).get(skill)
  if declared!=correct/n:errors.append(skill+":"+arm+":aggregate")
route=r.get("checks",{}).get("invalid_routes",{})
if not route or any(v!="YIELD" for v in route.values()):errors.append("invalid_routes")
m=r.get("measurements",{})
if m.get("adapter_setup_ms") is None or not isinstance(m.get("adapter_setup_ms"),(int,float)) or m["adapter_setup_ms"]<0:errors.append("adapter_setup")
updates=m.get("update_ms",{})
if set(updates)!={"global_B","global_C","adapter_B","adapter_C"} or any(not isinstance(v,(int,float)) or v<0 for v in updates.values()):errors.append("update_timing")
checks=r.get("checks",{})
if checks.get("base_immutable") is not True or checks.get("all_snapshot_roundtrip_exact") is not True or checks.get("all_rollbacks_exact") is not True:errors.append("state_integrity")
for name,snap in r.get("measurements",{}).get("snapshots",{}).items():
 try:
  learned_bytes=base64.b64decode(snap["state_b64"],validate=True)
  initial_bytes=base64.b64decode(snap["initial_state_b64"],validate=True)
  learned=torch.load(io.BytesIO(learned_bytes),map_location="cpu",weights_only=True)
  initial=torch.load(io.BytesIO(initial_bytes),map_location="cpu",weights_only=True)
  if hashlib.sha256(learned_bytes).hexdigest()!=snap.get("sha256"):errors.append(name+":learned_sha")
  if hashlib.sha256(initial_bytes).hexdigest()!=snap.get("initial_sha256"):errors.append(name+":initial_sha")
  if list(learned)!=list(initial):errors.append(name+":state_keys")
  for k in learned:
   if learned[k].dtype!=initial[k].dtype or learned[k].shape!=initial[k].shape:errors.append(name+":"+k+":state_meta")
   if k.startswith("core.") and not torch.equal(learned[k],initial[k]):errors.append(name+":"+k+":frozen_core_mutated")
 except Exception as exc:errors.append(name+":state_decode:"+type(exc).__name__)
quality=all(m.get("routed_accuracy",{}).get(k,0)>=.90 for k in ("A","B","C"))
shared=m.get("shared_sequential_accuracy",{})
routing_advantage=any(shared.get(k,1)>=0 and shared.get(k,1)<.90 for k in ("B","C"))
if errors: decision="FAIL_ROUTE_OR_AUDIT_INTEGRITY"
elif not quality: decision="FAIL_MULTI_SKILL_INTERFERENCE"
elif not routing_advantage: decision="HOLD_NO_ROUTING_ADVANTAGE"
else: decision="PASS_MULTI_SKILL_ROUTING_SCOPED"
print(json.dumps({"disposition":decision,"integrity":not errors,"errors":sorted(errors),"rows_recomputed":sum(len(stored.get(a,{}).get(k,{}).get("predicted",[])) for a in ("routed","shared") for k in specs),"routed_accuracy":m.get("routed_accuracy"),"shared_sequential_accuracy":m.get("shared_sequential_accuracy"),"quality_gate":quality,"routing_advantage_gate":routing_advantage},sort_keys=True,separators=(",",":")))
