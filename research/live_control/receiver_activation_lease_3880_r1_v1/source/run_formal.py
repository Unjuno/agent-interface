from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
ARMS=["TRANSLATED_LOWER","RECEIVER_ACTIVATION_TOKEN"]
CONDS=["BASELINE","INBOUND_QUEUE_80MS","PROCESSING_80MS","OUTBOUND_QUEUE_80MS","STALE_300MS"]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); a=ap.parse_args(); root=Path(a.out); root.mkdir(parents=True,exist_ok=False)
 cases=[]; runner=Path(__file__).with_name("run_case.py")
 for rep in range(2):
  for cond in CONDS:
   for arm in ARMS:
    cid=f"{arm}-{cond}-r{rep}"; dest=root/cid
    start=time.perf_counter_ns(); p=subprocess.run([sys.executable,"-S","-B",str(runner),"--arm",arm,"--condition",cond,"--rep",str(rep),"--out",str(dest)],capture_output=True,text=True,timeout=5)
    end=time.perf_counter_ns(); row={"case_id":cid,"exit":p.returncode,"stdout":p.stdout,"stderr":p.stderr,"start_ns":start,"end_ns":end}
    cases.append(row); (root/"progress.json").write_text(json.dumps(cases,sort_keys=True,indent=2)+"\n")
    if p.returncode!=0: return p.returncode
 (root/"launcher.json").write_text(json.dumps({"cases":cases,"count":len(cases)},sort_keys=True,indent=2)+"\n")
 return 0
if __name__=="__main__": raise SystemExit(main())
