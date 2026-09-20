from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
F=Path(sys.argv[1]);O=Path(sys.argv[2]);H="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 rb=(F/"raw.json").read_bytes();r=json.loads(rb);err=[];find=[]
 if r.get("allocation")!="issue3733-german-xkb-apply-diagnostic-formal-01":err.append("allocation")
 if r.get("image")!=H or r.get("network")!="none":err.append("environment")
 actual={}
 for p in sorted(F.rglob("*")):
  if p.is_symlink():err.append("symlink")
  elif p.is_file() and p.name!="raw.json":actual[p.relative_to(F).as_posix()]=sha(p.read_bytes())
 if actual!=r.get("artifact_sha256"):err.append("artifact_inventory")
 rows=r.get("rows",[])
 if not rows or rows[0].get("case")!="german":find.append("german_row")
 for row in rows:
  if not row.get("xvfb_process",{}).get("reaped"):find.append("process_cleanup")
  if not all(row.get("extensions",{}).values()):find.append("extensions")
 de=rows[0] if rows else {}
 if de.get("apply",{}).get("argv")!=["setxkbmap","-display",de.get("display"),"-verbose","10","-layout","de"]:find.append("explicit_target_argv")
 if de.get("status")!="OBSERVED" or de.get("query_layout")!="de":find.append("layout_unresolved")
 if de.get("changed",{}).get("xkbcomp") is not True:find.append("server_dump_not_changed")
 if len(rows)==2:
  if rows[1].get("case")!="us-control" or rows[1].get("status")!="CONTROL":find.append("control")
 elif not de.get("status","").startswith("STOP_"):find.append("incomplete")
 disp="FAIL_AUDIT_INTEGRITY" if err else "STOP_DIAGNOSTIC" if find else "PASS_DIAGNOSTIC_SCOPED"
 out={"allocation":"issue3733-german-xkb-apply-diagnostic-formal-01","disposition":disp,"formal_raw_sha256":sha(rb),"auditor_sha256":sha(Path(__file__).read_bytes()),"integrity_errors":err,"findings":find,"artifact_files_checked":len(actual),"rows":[{"case":x.get("case"),"status":x.get("status"),"query_layout":x.get("query_layout"),"changed":x.get("changed")} for x in rows]}
 O.mkdir(parents=True,exist_ok=True);(O/"independent.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,sort_keys=True));return 1 if err else 0
if __name__=="__main__":raise SystemExit(main())
