#!/usr/bin/env python3
import argparse, json, subprocess, sys, time
from pathlib import Path
from worker import POLICIES, SCENARIOS

def run(batch, kind, outdir):
    outdir.mkdir(parents=True,exist_ok=False)
    rows=[]; failures=[]
    for policy in POLICIES:
      for scenario in SCENARIOS:
        cid=f'{kind}-r{batch}-{policy}-{scenario}'
        cmd=[sys.executable,'-B',str(Path(__file__).with_name('worker.py')),'--case-id',cid,'--policy',policy,'--scenario',scenario]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=3)
        rec={'case_id':cid,'policy':policy,'scenario':scenario,'argv':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        if p.returncode==0:
            try: rec['result']=json.loads(p.stdout)
            except Exception as e: rec['parse_error']=repr(e); failures.append(cid)
        else: failures.append(cid)
        rows.append(rec)
    (outdir/'RAW.json').write_text(json.dumps({'schema':'agent-interface/referenced-image-ack-gc-raw-v1','kind':kind,'batch':batch,'rows':rows},indent=2,sort_keys=True)+'\n')
    receipt={'kind':kind,'batch':batch,'cases':len(rows),'failures':failures,'runner_exit':0 if not failures else 2,'ended_ns':time.monotonic_ns()}
    (outdir/'EXECUTION.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,sort_keys=True)); return receipt['runner_exit']

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('kind',choices=['construction','formal']); ap.add_argument('batch',type=int); ap.add_argument('outdir')
    a=ap.parse_args(); raise SystemExit(run(a.batch,a.kind,Path(a.outdir)))
if __name__=='__main__': main()
