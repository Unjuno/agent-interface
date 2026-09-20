from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

FORMAL=Path(sys.argv[1]); OUT=Path(sys.argv[2])

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def main()->int:
    raw_bytes=(FORMAL/"raw.json").read_bytes(); raw=json.loads(raw_bytes)
    errors=[]; findings=[]
    if raw.get("allocation")!="issue3733-german-xkb-map-diagnostic-formal-01": errors.append("allocation")
    if raw.get("base_commit")!="e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8": errors.append("base")
    if raw.get("image")!="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27" or raw.get("network")!="none": errors.append("environment")
    found={}
    for p in sorted(FORMAL.rglob("*")):
        if p.is_symlink(): errors.append("symlink")
        elif p.is_file() and p.name!="raw.json": found[p.relative_to(FORMAL).as_posix()]=sha(p.read_bytes())
    if found!=raw.get("artifact_sha256"): errors.append("artifact_inventory")
    if [r.get("case") for r in raw.get("rows",[])]!=["german","us-control"]: findings.append("row_schedule")
    if len(raw.get("rows",[]))==2:
        de,us=raw["rows"]
        if de.get("query_layout")!="de" or de.get("status")!="OBSERVED": findings.append("german_row")
        if us.get("query_layout")!="us" or us.get("status")!="CONTROL": findings.append("control_row")
        for row in raw["rows"]:
            if not row.get("xvfb_process",{}).get("reaped"): findings.append("xvfb_cleanup")
        if de.get("methods_changed",{}).get("xkbcomp")!=de.get("methods_changed",{}).get("xmodmap"): findings.append("independent_server_views_disagree")
        if de.get("methods_changed",{}).get("xmodmap")!=de.get("methods_changed",{}).get("xlib_full_map"): findings.append("core_map_views_disagree")
        if not (de.get("methods_changed",{}).get("xlib_selected_symbols")): findings.append("selected_symbols_unchanged")
        if any(not isinstance(de.get("after",{}).get(k,{}).get("stdout"),str) for k in ("query","xkbcomp","xmodmap")): findings.append("raw_capture_missing")
    else: findings.append("row_count")
    disposition="FAIL_AUDIT_INTEGRITY" if errors else "STOP_DIAGNOSTIC" if findings else "PASS_DIAGNOSTIC_SCOPED"
    result={"allocation":"issue3733-german-xkb-map-diagnostic-formal-01","disposition":disposition,"formal_raw_sha256":sha(raw_bytes),"source_files_checked":0,"artifact_files_checked":len(found),"integrity_errors":errors,"findings":findings,"rows":[{"case":r.get("case"),"status":r.get("status")} for r in raw.get("rows",[])]}
    OUT.mkdir(parents=True,exist_ok=True); (OUT/"independent.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True)); return 1 if errors else 0

if __name__=="__main__":raise SystemExit(main())
