from __future__ import annotations
import hashlib, json, random, sys

ROLES=("HINT","PLANNER_CONTEXT","INVALIDATOR","EFFECT_EVIDENCE","ADMISSION_DEPENDENCY")
FRESH=("CURRENT","HISTORICAL")
SEED=156020260918001; CASES=20000; NOW0=1_000_000_000

def add(h,row): h.update(json.dumps(row,sort_keys=True,separators=(",",":")).encode()); h.update(b"\n")

def expected():
 rng=random.Random(SEED); h=hashlib.sha256(); c={k:0 for k in ["weak_direct_reject","valid_admit","historical_or_expired_reject","planner_projection","roundtrip","revalidate_success","revalidate_reject","invalid_backend_emission","role_escape","provenance_mutation"]}
 for idx in range(CASES):
  t=rng.randrange(6); now=NOW0+rng.randrange(0,10000); ent=f"e{rng.randrange(8)}"; surf=f"s{rng.randrange(4)}"; bbox=[rng.randrange(0,500),rng.randrange(0,300),rng.randrange(5,80),rng.randrange(5,80)]; snap=rng.randrange(0,4); row={"i":idx,"t":t,"snap":snap}
  if t==0:
   role=rng.choice(["HINT","PLANNER_CONTEXT","INVALIDATOR","EFFECT_EVIDENCE"]); fresh=rng.choice(FRESH); c["roundtrip"]+=snap; c["weak_direct_reject"]+=1; row.update({"role":role,"f":fresh,"a":False,"b":0})
  elif t==1:
   fresh=rng.choice(FRESH); expired=bool(rng.randrange(2))
   # Consume the same validity-horizon draw as the frozen formal generator.
   if expired: rng.randrange(10)
   else: rng.randrange(100)
   c["roundtrip"]+=snap; admitted=(fresh=="CURRENT" and not expired); c["valid_admit" if admitted else "historical_or_expired_reject"]+=1; row.update({"f":fresh,"x":expired,"a":admitted,"b":1 if admitted else 0})
  elif t==2:
   role=rng.choice(ROLES); fresh=rng.choice(FRESH); c["roundtrip"]+=snap; c["planner_projection"]+=1; row.update({"role":role,"f":fresh,"ok":True})
  elif t==3:
   c["roundtrip"]+=snap; c["revalidate_success"]+=1; row.update({"a":True,"src":f"cur{idx}","bb":bbox})
  elif t==4:
   mismatch=rng.choice(["entity","surface","expired"]); c["roundtrip"]+=snap; c["revalidate_reject"]+=1; row.update({"m":mismatch,"ok":True})
  else:
   n=1+rng.randrange(5)
   records=[]
   for j in range(n):
    role=rng.choice(ROLES); fresh=rng.choice(FRESH)
    records.append({"record_id":f"r{idx}-{j}","entity_id":ent,"surface_id":surf,"bbox":[bbox[0]+j,bbox[1],bbox[2],bbox[3]],"role":role,"freshness":fresh,"source_id":f"src{idx}-{j}","observed_ns":now-100,"valid_until_ns":now+100,"input_authority":False,"semantic_authority":False,"created_by":"INGEST"})
   canonical={"schema":"persistent-geometric-state-v1","records":sorted(records,key=lambda r:r["record_id"])}
   blob=json.dumps(canonical,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
   c["roundtrip"]+=1
   row.update({"n":n,"ok":True,"sha":hashlib.sha256(blob).hexdigest()[:16]})
  add(h,row)
 return c,h.hexdigest()

def audit(r):
 errs=[]; exp_counts,partial_digest=expected()
 if r.get("schema")!="pgws-role-safety-formal-v1": errs.append("schema")
 if r.get("task")!="PERSISTENT-GEOMETRIC-STATE-ROLE-SAFETY-20260918-001": errs.append("task")
 if r.get("seed")!=SEED or r.get("random_cases")!=CASES: errs.append("allocation")
 if r.get("formal_invocations")!=1 or any(r.get(k)!=0 for k in ("reruns","replacements","tuning")): errs.append("invocation")
 if r.get("directed_rows")!=20 or r.get("directed_invalid_backend_emissions")!=0 or r.get("directed_expectation_mismatches")!=0: errs.append("directed")
 if r.get("counts")!=exp_counts: errs.append("counts")
 if r.get("row_digest_sha256")!=partial_digest: errs.append("row_digest")
 c=r.get("counts",{})
 for k in ("invalid_backend_emission","role_escape","provenance_mutation"):
  if c.get(k)!=0: errs.append(k)
 for k in ("weak_direct_reject","planner_projection","revalidate_success","revalidate_reject"):
  if c.get(k,0)<=1000: errs.append("coverage_"+k)
 if c.get("valid_admit",0)<=500 or c.get("historical_or_expired_reject",0)<=500 or c.get("roundtrip",0)<=10000: errs.append("coverage")
 if r.get("decision")!="PASS_PERSISTENT_GEOMETRIC_STATE_ROLE_SAFETY_SCOPED": errs.append("decision")
 return {"schema":"pgws-role-safety-audit-v2","pass":not errs,"errors":errs,"semantic_counts_recomputed":True,"row_digest_recomputed_sha256":partial_digest}

if __name__=="__main__":
 r=json.load(open(sys.argv[1] if len(sys.argv)>1 else "FORMAL_RESULT.json")); out=audit(r); open("AUDIT.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
