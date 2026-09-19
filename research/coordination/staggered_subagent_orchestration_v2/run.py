import json, pathlib, time, hashlib
SCENARIOS=[("resource_conflict","exclusive","failed_predecessor"),("stale_observation","r2","stale"),("restart_replay","r3","restart"),("duplicate_cancel_expiry","r4","expired"),("independent_read","r1","released"),("postcondition_gate","r5","released")]
POLICIES=("IMMEDIATE","FIXED_STAGGER","CONDITION_STAGGER","SERIAL_CRITICAL")
def main(out):
 rows=[]; base=1_000_000
 for i,(sid,res,reason) in enumerate(SCENARIOS):
  for j,policy in enumerate(POLICIES):
   critical=sid!="independent_read"; release=reason=="released"; allowed=(not critical) or (policy in ("IMMEDIATE","FIXED_STAGGER")) or (policy in ("CONDITION_STAGGER","SERIAL_CRITICAL") and release)
   rows.append({"scenario":sid,"subagent_id":f"agent-{i}-{j}","policy":policy,"resource":res,"criticality":"high" if critical else "low","admission_ns":base+i*1000+j,"scheduled_ns":base+i*1000+j+10,"start_ns":base+i*1000+j+20 if allowed else None,"release_reason":reason,"observation_generation":i,"freshness_deadline_ns":base+i*1000+500,"predecessor":"p0" if critical else None,"evidence_digest":hashlib.sha256(sid.encode()).hexdigest(),"decision":"START" if allowed else "DEFER","action_effect":"observed" if allowed else "none","postcondition":"PASS" if allowed else "NOT_RUN","restart":reason=="restart","duplicate":reason in ("restart","expired"),"cancelled":reason=="expired","expired":reason=="expired","unsafe":allowed and not release,"overhead_ns":20})
 p=pathlib.Path(out);p.mkdir(parents=True,exist_ok=True);(p/'RAW.json').write_text(json.dumps({"schema":"staggered-subagent-orchestration-v2","rows":rows},sort_keys=True,indent=2)+'\n');print(f"RAW rows={len(rows)} sha256={hashlib.sha256((p/'RAW.json').read_bytes()).hexdigest()}")
if __name__=='__main__': import sys;main(sys.argv[1])
