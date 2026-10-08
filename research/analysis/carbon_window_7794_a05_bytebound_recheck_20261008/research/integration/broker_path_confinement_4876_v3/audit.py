from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
EXPECTED={"repo-alias":True,"workspace-alias":True,"root-alias":True,"in-root-symlink":True,"absolute-host":True,"parent-traversal":True,"encoded-traversal":True,"backslash-traversal":True,"external-symlink":True,"missing":True}
def main(raw:Path,out:Path)->int:
 data=raw.read_bytes(); r=json.loads(data); errors=[]
 if r.get("allocation")!="broker-path-confinement-4876-20260927-03":errors.append("allocation")
 if r.get("source_blob")!="5734f54f318db9ac5e96b2bed6f6bed105ac39ff":errors.append("source_blob")
 cases={x.get("name"):x for x in r.get("cases",[])}
 if set(cases)!=set(EXPECTED):errors.append("case_set")
 for name in EXPECTED:
  if name not in cases or cases[name].get("pass") is not True:errors.append("case:"+name)
 if r.get("case_count")!=10:errors.append("case_count")
 if r.get("subprocess_calls")!=1 or r.get("valid_broker_returncode")!=0:errors.append("serve_valid_once")
 if r.get("authority_granted") is not False:errors.append("authority")
 if r.get("decision")!="PASS_PATH_RESOLVER_CONSTRUCTION_SCOPED":errors.append("decision")
 report={"schema":"broker-path-confinement-4876-independent-audit-v2","raw_sha256":hashlib.sha256(data).hexdigest(),"rows":r.get("case_count"),"errors":errors,"decision":"PASS_INDEPENDENT_AUDIT" if not errors else "HOLD_AUDIT"}
 out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,sort_keys=True));return 0 if not errors else 1
if __name__=="__main__":raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))





