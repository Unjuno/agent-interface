"""Independent raw-only oracle, not importing the candidate implementation."""
import hashlib,json,sys
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def shabytes(x): return hashlib.sha256(x).hexdigest()
def oracle(row):
 p=row["proposal"]
 ok=(row["stratum"]=="CURRENT_VALID" and row["active_generation"]==2 and p.get("schema")=="unjuno.system1.proposal-envelope.v1" and p.get("captured_generation")==2 and p.get("intent_version")=="intent-v4" and p.get("scope")=="skill/needle-correction" and p.get("evidence_generation")==41 and p.get("update_lineage")=="COMMITTED" and p.get("calibration")=="VALID" and p.get("adapter_digest")=="a"*64 and p.get("confidence")==.99)
 return "ELIGIBLE_PROPOSAL_ONLY" if ok else "YIELD"
def candidate_independent(p):
 keys={"schema","proposal_id","captured_generation","intent_version","scope","evidence_generation","update_lineage","calibration","adapter_digest","confidence"}
 if type(p)!=dict or set(p)!=keys:return "YIELD"
 if p["schema"]!="unjuno.system1.proposal-envelope.v1" or type(p["captured_generation"])!=int or p["captured_generation"]!=2:return "YIELD"
 if p["intent_version"]!="intent-v4" or p["scope"]!="skill/needle-correction":return "YIELD"
 if type(p["evidence_generation"])!=int or p["evidence_generation"]!=41:return "YIELD"
 if p["update_lineage"]!="COMMITTED" or p["calibration"]!="VALID" or p["adapter_digest"]!="a"*64:return "YIELD"
 if type(p["confidence"]) not in (int,float) or not .90<=p["confidence"]<=1:return "YIELD"
 return "ELIGIBLE_PROPOSAL_ONLY"
def main(path,source_hash):
 raw=open(path,"rb").read(); d=json.loads(raw); errors=[]; rows=d.get("rows",[]); controls=d.get("controls",[]); counts={}
 if len(rows)!=64:errors.append("rows")
 if len(controls)<12:errors.append("controls")
 for r in rows:
  s=r.get("stratum"); counts[s]=counts.get(s,0)+1; want=oracle(r)
  if r.get("oracle_label")!=want:errors.append("label:"+str(r.get("row_id")))
  if r.get("validation_envelope")!=candidate_independent(r["proposal"]):errors.append("candidate:"+str(r.get("row_id")))
  if r.get("validation_envelope")!=want:errors.append("oracle_disagreement:"+str(r.get("row_id")))
  if r.get("grants_authority") is not False:errors.append("authority_flag")
  base="ELIGIBLE_PROPOSAL_ONLY" if type(r["proposal"].get("confidence")) in (int,float) and r["proposal"]["confidence"]>=.90 else "YIELD"
  if r.get("confidence_only")!=base:errors.append("baseline")
 if len(counts)!=8 or any(x!=8 for x in counts.values()):errors.append("strata_balance")
 names=set()
 for c in controls:
  names.add(c.get("control")); p=c["proposal"]
  if candidate_independent(p)!="YIELD" or c.get("validation_envelope")!="YIELD":errors.append("control_accept:"+str(c.get("control")))
  if c.get("state_mutation") is not False or c.get("authority_granted") is not False:errors.append("control_effect")
  if c.get("proposal_sha256")!=shabytes(canon(p)):errors.append("control_digest")
 if len(names)!=len(controls):errors.append("duplicate_controls")
 unsafe=sum(r["validation_envelope"]!="YIELD" for r in rows if r["stratum"]!="CURRENT_VALID")
 over=sum(r["validation_envelope"]=="YIELD" for r in rows if r["stratum"]=="CURRENT_VALID")
 baseline_bad=sum(r["confidence_only"]!="YIELD" for r in rows if r["stratum"]!="CURRENT_VALID")
 if unsafe:errors.append("unsafe_eligibility")
 if over:errors.append("known_good_false_yield")
 if baseline_bad<40:errors.append("weak_comparator")
 if d.get("issue")!=4840 or d.get("intake_main")!="a07fa7c1539316d9f951767649c6555d63faf10b":errors.append("intake")
 if d.get("image_id")!="sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e":errors.append("image")
 if d.get("formal_trainer_invocations")!=1 or d.get("training_updates")!=0 or d.get("network")!="none":errors.append("execution")
 if d.get("source_sha256")!=source_hash:errors.append("source_hash")
 claimed=d.get("raw_sha256"); unsigned=dict(d);unsigned.pop("raw_sha256",None)
 if claimed!=shabytes(canon(unsigned)):errors.append("raw_hash")
 report={"disposition":"PASS_GENERATION_FENCE_SCOPED" if not errors else "FAIL_AUDIT","errors":errors,"rows":len(rows),"strata":counts,"controls":len(controls),"known_good_false_yield":over,"unsafe_eligibility":unsafe,"confidence_only_negative_eligibility":baseline_bad,"authority_grants":0,"training_updates":0,"raw_sha256":shabytes(raw)}
 print(json.dumps(report,sort_keys=True,separators=(",",":")));return 0 if not errors else 1
if __name__=="__main__":raise SystemExit(main(sys.argv[1],sys.argv[2]))
