"""Finite generation-fence study; no model fitting or authority."""
import hashlib,json,sys
SCHEMA="unjuno.system1.proposal-envelope.v1"
ALLOCATION="needle-adaptive-generation-fence-4840-v1"
IMAGE_ID="sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
STRATA=("CURRENT_VALID","OLD_INFLIGHT_AFTER_SWITCH","DELAYED_OLD_REPLY","REPLAYED_PRE_ROLLBACK_GENERATION","FUTURE_GENERATION","INTENT_MISMATCH","SCOPE_OR_EVIDENCE_MISMATCH","UPDATE_LINEAGE_OR_CALIBRATION_INVALID")
FIELDS={"schema","proposal_id","captured_generation","intent_version","scope","evidence_generation","update_lineage","calibration","adapter_digest","confidence"}
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def sha(x): return hashlib.sha256(x).hexdigest()
def objsha(x): return sha(canon(x))
def proposal(stratum,i):
 p={"schema":SCHEMA,"proposal_id":f"{stratum.lower()}-{i:02d}","captured_generation":2,"intent_version":"intent-v4","scope":"skill/needle-correction","evidence_generation":41,"update_lineage":"COMMITTED","calibration":"VALID","adapter_digest":"a"*64,"confidence":0.99}
 if stratum in ("OLD_INFLIGHT_AFTER_SWITCH","DELAYED_OLD_REPLY"): p["captured_generation"]=1
 elif stratum=="REPLAYED_PRE_ROLLBACK_GENERATION": p["captured_generation"]=0
 elif stratum=="FUTURE_GENERATION": p["captured_generation"]=3
 elif stratum=="INTENT_MISMATCH": p["intent_version"]="intent-other"
 elif stratum=="SCOPE_OR_EVIDENCE_MISMATCH":
  if i%2: p["scope"]="skill/other"
  else: p["evidence_generation"]=40
 elif stratum=="UPDATE_LINEAGE_OR_CALIBRATION_INVALID":
  if i%2: p["update_lineage"]="PENDING"
  else: p["calibration"]="EXPIRED"
 return p
def envelope(p):
 if type(p)!=dict or set(p)!=FIELDS: return "YIELD"
 if p["schema"]!=SCHEMA or type(p["captured_generation"])!=int or p["captured_generation"]!=2: return "YIELD"
 if p["intent_version"]!="intent-v4" or p["scope"]!="skill/needle-correction": return "YIELD"
 if type(p["evidence_generation"])!=int or p["evidence_generation"]!=41: return "YIELD"
 if p["update_lineage"]!="COMMITTED" or p["calibration"]!="VALID" or p["adapter_digest"]!="a"*64: return "YIELD"
 if type(p["confidence"]) not in (int,float) or not 0.90<=p["confidence"]<=1: return "YIELD"
 return "ELIGIBLE_PROPOSAL_ONLY"
def confidence_only(p):
 c=p.get("confidence") if type(p)==dict else None
 return "ELIGIBLE_PROPOSAL_ONLY" if type(c) in (int,float) and c>=.90 else "YIELD"
def mutations():
 b=proposal("CURRENT_VALID",0); out=[]
 changes=[("replay_previous",lambda p:p.update(captured_generation=1)),("replay_zero",lambda p:p.update(captured_generation=0)),("future_generation",lambda p:p.update(captured_generation=3)),("stale_evidence",lambda p:p.update(evidence_generation=40)),("future_evidence",lambda p:p.update(evidence_generation=42)),("intent_swap",lambda p:p.update(intent_version="other")),("scope_swap",lambda p:p.update(scope="other")),("lineage_pending",lambda p:p.update(update_lineage="PENDING")),("lineage_unknown",lambda p:p.update(update_lineage="UNKNOWN")),("calibration_expired",lambda p:p.update(calibration="EXPIRED")),("digest_mismatch",lambda p:p.update(adapter_digest="b"*64)),("low_confidence",lambda p:p.update(confidence=.89)),("missing_scope",lambda p:p.pop("scope")),("unknown_field",lambda p:p.update(grants_authority=True)),("non_numeric_confidence",lambda p:p.update(confidence="0.99"))]
 for name,change in changes:
  p=dict(b); change(p); out.append({"control":name,"proposal":p})
 return out
def run():
 rows=[]
 for s in STRATA:
  for i in range(8):
   p=proposal(s,i); label="ELIGIBLE_PROPOSAL_ONLY" if s=="CURRENT_VALID" else "YIELD"
   rows.append({"row_id":p["proposal_id"],"stratum":s,"repetition":i,"active_generation":2,"previous_generation":1,"rollback_generation":2,"proposal":p,"oracle_label":label,"confidence_only":confidence_only(p),"validation_envelope":envelope(p),"grants_authority":False})
 controls=[]
 for x in mutations():
  p=x["proposal"]; controls.append({"control":x["control"],"proposal":p,"proposal_sha256":objsha(p),"validation_envelope":envelope(p),"state_mutation":False,"authority_granted":False})
 return {"schema":"unjuno.needle.generation-fence-result.v1","allocation":ALLOCATION,"issue":4840,"intake_main":"a07fa7c1539316d9f951767649c6555d63faf10b","image_id":IMAGE_ID,"platform":"linux/amd64","invocation_id":"formal-once-4840-20260927","formal_trainer_invocations":1,"training_updates":0,"network":"none","limits":{"cpus":1,"memory":"2g","pids":64,"root_read_only":True,"source_read_only":True},"transition":{"previous_generation":1,"activated_generation":1,"rollback_generation":2,"active_generation":2,"rollback_is_new_generation":True},"rows":rows,"controls":controls}
if __name__=="__main__":
 r=run(); r["source_sha256"]=sha(open(__file__,"rb").read()); r["raw_sha256"]=objsha(r)
 with open(sys.argv[1],"wb") as f:f.write(canon(r)+b"\n")
 print(json.dumps({"allocation":ALLOCATION,"rows":len(r["rows"]),"controls":len(r["controls"]),"source_sha256":r["source_sha256"],"raw_sha256":r["raw_sha256"]},sort_keys=True))
