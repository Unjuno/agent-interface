#!/usr/bin/env python3
import argparse, json, subprocess, sys, time
from pathlib import Path
from worker import POLICIES,SCENARIOS

def run(kind,batch,outdir):
    outdir.mkdir(parents=True,exist_ok=False); rows=[]; fails=[]
    for p in POLICIES:
      for s in SCENARIOS:
        cid=f'{kind}-r{batch}-{p}-{s}'
        cmd=[sys.executable,'-B',str(Path(__file__).with_name('worker.py')),'--case-id',cid,'--policy',p,'--scenario',s]
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=12)
        rec={'case_id':cid,'policy':p,'scenario':s,'argv':cmd,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}
        if cp.returncode==0:
          try: rec['result']=json.loads(cp.stdout)
          except Exception as e: rec['parse_error']=repr(e); fails.append(cid)
        else: fails.append(cid)
        rows.append(rec)
    raw={'schema':'agent-interface/referenced-image-gc-concurrency-raw-v1','kind':kind,'batch':batch,'rows':rows}
    (outdir/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    ex={'kind':kind,'batch':batch,'cases':len(rows),'failures':fails,'runner_exit':0 if not fails else 2,'ended_ns':time.monotonic_ns()}
    (outdir/'EXECUTION.json').write_text(json.dumps(ex,indent=2,sort_keys=True)+'\n'); print(json.dumps(ex,sort_keys=True)); return ex['runner_exit']

def main():
    a=argparse.ArgumentParser(); a.add_argument('kind',choices=['construction','formal']); a.add_argument('batch',type=int); a.add_argument('outdir'); x=a.parse_args(); raise SystemExit(run(x.kind,x.batch,Path(x.outdir)))
if __name__=='__main__': main()
