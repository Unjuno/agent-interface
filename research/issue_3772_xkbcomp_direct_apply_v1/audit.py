from __future__ import annotations
import hashlib,json,re,sys
from pathlib import Path
F=Path(sys.argv[1]);O=Path(sys.argv[2]);IMAGE="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 rb=(F/"raw.json").read_bytes();r=json.loads(rb);err=[];find=[]
 if r.get("allocation")!="issue3733-german-xkb-xkbcomp-apply-formal-01":err.append("allocation")
 if r.get("image")!=IMAGE or r.get("network")!="none":err.append("environment")
 actual={}
 for p in sorted(F.rglob("*")):
  if p.is_symlink():err.append("symlink")
  elif p.is_file() and p.name!="raw.json":actual[p.relative_to(F).as_posix()]=sha(p.read_bytes())
 if actual!=r.get("artifact_sha256"):err.append("artifact_inventory")
 rows=r.get("rows",[])
 if not rows or rows[0].get("case")!="german":find.append("german_row")
 for x in rows:
  if not x.get("xvfb_process",{}).get("reaped"):find.append("cleanup")
  if not all(x.get("extensions",{}).values()):find.append("extensions")
 de=rows[0] if rows else {};gen=de.get("generate",{});app=de.get("direct_apply",{});disp=de.get("display")
 if gen.get("argv")!=["setxkbmap","-display",disp,"-print","-layout","de"]:find.append("generated_argv")
 if app.get("argv")!=["xkbcomp","-w","0","-",disp]:find.append("apply_argv")
 if de.get("status")!="OBSERVED" or de.get("query_layout")!="de":find.append("German_not_active")
 if len(rows)==2 and rows[1].get("status")!="CONTROL":find.append("US_control")
 elif len(rows)<2 and not de.get("status","").startswith("STOP_"):find.append("schedule")
 dispn="FAIL_AUDIT_INTEGRITY" if err else "STOP_DIAGNOSTIC" if find else "PASS_DIAGNOSTIC_SCOPED"
 result={"allocation":"issue3733-german-xkb-xkbcomp-apply-formal-01","disposition":dispn,"formal_raw_sha256":sha(rb),"auditor_sha256":sha(Path(__file__).read_bytes()),"integrity_errors":err,"findings":find,"artifact_files_checked":len(actual),"rows":[{"case":x.get("case"),"status":x.get("status"),"query_layout":x.get("query_layout"),"direct_apply_returncode":x.get("direct_apply",{}).get("returncode")} for x in rows]}
 O.mkdir(parents=True,exist_ok=True);(O/"independent.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,sort_keys=True));return 1 if err else 0
if __name__=="__main__":raise SystemExit(main())
