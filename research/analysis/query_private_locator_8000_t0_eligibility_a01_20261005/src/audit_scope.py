"""Read-only bounded search for retained cross-worker lookup traces in research."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(sys.argv[1])
INCLUDE={".md",".json",".jsonl",".py",".txt",".yaml",".yml",".csv"}
EXCLUDE_PARTS={".git","__pycache__","source_bundle","decoded_material","images","node_modules"}
MAX_FILE=64*1024*1024
MAX_TOTAL=1024*1024*1024
PATTERNS=[
    r"cross[- ]worker.{0,80}(retriev|lookup|holder|artifact)",
    r"(retriev|lookup|holder|artifact).{0,80}cross[- ]worker",
    r"claim[- ]dependent.{0,80}(retriev|lookup)",
    r"evidence[- ]location|artifact[- ]locator|query[- ]private",
    r"broadcast.{0,80}reacquisition|reacquisition.{0,80}broadcast",
    r"who currently holds.{0,80}(evidence|artifact)",
]
RX=[re.compile(p,re.I) for p in PATTERNS]

def main():
    files=[]; skipped=[]; total=0; matches=[]; bytes_scanned=0
    tracked=subprocess.check_output(["git","ls-files","research/"],cwd=ROOT,text=True).splitlines()
    for rel in sorted(tracked):
        p=ROOT/rel
        if p.suffix.lower() not in INCLUDE or any(part in EXCLUDE_PARTS for part in p.parts): continue
        try: size=p.stat().st_size
        except OSError: continue
        if size>MAX_FILE or total+size>MAX_TOTAL:
            skipped.append({"path":str(p.relative_to(ROOT)),"size":size,"reason":"size_cap"}); continue
        total+=size
        try: data=p.read_text(encoding="utf-8",errors="replace")
        except OSError as e:
            skipped.append({"path":str(p.relative_to(ROOT)),"size":size,"reason":type(e).__name__}); continue
        bytes_scanned+=size; files.append(str(p.relative_to(ROOT)))
        for no,line in enumerate(data.splitlines(),1):
            if any(rx.search(line) for rx in RX):
                matches.append({"path":str(p.relative_to(ROOT)),"line":no,"snippet":line[:240]})
    try:
        main=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    except Exception: main="unavailable"
    result={"disposition":"HOLD_NO_ELIGIBLE_LOOKUP","scope":{"repository_subtree":"research/","extensions":sorted(INCLUDE),"max_file_bytes":MAX_FILE,"max_total_bytes":MAX_TOTAL,"excluded_parts":sorted(EXCLUDE_PARTS),"patterns":PATTERNS},"base_commit":main,"files_scanned":len(files),"bytes_scanned":bytes_scanned,"files_size_skipped":len(skipped),"skipped_files":skipped,"match_count":len(matches),"matches":matches,"eligibility_rule":"source-bound artifact held by one worker + a distinct worker's genuine claim-dependent retrieval opportunity + observable discovery/reacquisition outcome or cost","note":"Matches are leads, not qualifying traces. Each possible record must be manually checked against the three-part eligibility rule; prior proposals/contracts do not establish an executed retrieval opportunity."}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("disposition","base_commit","files_scanned","bytes_scanned","files_size_skipped","match_count")},sort_keys=True))
if __name__=="__main__": main()
