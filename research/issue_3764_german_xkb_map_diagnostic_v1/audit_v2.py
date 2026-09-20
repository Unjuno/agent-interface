from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
FORMAL=Path(sys.argv[1]);OUT=Path(sys.argv[2])
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 rawb=(FORMAL/"raw.json").read_bytes();raw=json.loads(rawb);errors=[];findings=[]
 if raw.get("allocation")!="issue3733-german-xkb-map-diagnostic-formal-02":errors.append("allocation")
 if raw.get("base_commit")!="e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8":errors.append("base")
 if raw.get("image")!="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27" or raw.get("network")!="none":errors.append("environment")
 actual={}
 for p in sorted(FORMAL.rglob("*")):
  if p.is_symlink():errors.append("symlink")
  elif p.is_file() and p.name!="raw.json":actual[p.relative_to(FORMAL).as_posix()]=sha(p.read_bytes())
 if actual!=raw.get("artifact_sha256"):errors.append("artifact_inventory")
 rows=raw.get("rows",[])
 if [r.get("case") for r in rows]!=["german","us-control"]:findings.append("row_schedule")
 if len(rows)==2:
  de,us=rows
  if de.get("status")!="OBSERVED" or de.get("query_layout")!="de":findings.append("german_transition")
  if us.get("status")!="CONTROL" or us.get("query_layout")!="us":findings.append("us_control")
  for r in rows:
   if not r.get("xvfb_process",{}).get("reaped"):findings.append("process_cleanup")
   if r.get("status") in {"OBSERVED","CONTROL"} and not all(r.get("extensions",{}).values()):findings.append("extensions")
  if de.get("status")=="OBSERVED":
   if not de.get("changed",{}).get("server_dump"):findings.append("server_dump_unchanged")
   for tag in ("before","after"):
    for key in ("query","xkbcomp"):
     path=FORMAL/"german"/(f"{tag}.{key}.txt")
     if not path.is_file():findings.append("missing:"+str(path.relative_to(FORMAL)))
    xp=FORMAL/"german"/(f"{tag}.xlib.json")
    if not xp.is_file():findings.append("missing_xlib:"+tag)
    else:
     obj=json.loads(xp.read_text())
     if obj.get("mapping_sha256")!=de[tag]["xlib"]["mapping_sha256"]:findings.append("xlib_hash_mismatch:"+tag)
     if obj.get("selected")!=de[tag]["xlib"]["selected"]:findings.append("selected_map_mismatch:"+tag)
  if us.get("status")=="CONTROL":
   q=us.get("before",{}).get("query",{}).get("stdout","")
   if "layout:     us" not in q and "layout: us" not in q:findings.append("us_query")
 disposition="FAIL_AUDIT_INTEGRITY" if errors else "STOP_DIAGNOSTIC" if findings else "PASS_DIAGNOSTIC_SCOPED"
 result={"allocation":"issue3733-german-xkb-map-diagnostic-formal-02","disposition":disposition,"formal_raw_sha256":sha(rawb),"auditor_sha256":sha(Path(__file__).read_bytes()),"integrity_errors":errors,"findings":findings,"artifact_files_checked":len(actual),"rows":[{"case":r.get("case"),"status":r.get("status"),"changed":r.get("changed")} for r in rows]}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"independent.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,sort_keys=True));return 1 if errors else 0
if __name__=="__main__":raise SystemExit(main())
