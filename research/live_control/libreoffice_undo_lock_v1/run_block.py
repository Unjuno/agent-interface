#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    root=Path(args.root); out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    sched=json.loads((root/'schedule.json').read_text())['cases']
    ledger=[]
    for i,scenario in enumerate(sched):
        cid=f'{i:02d}-{scenario}'
        cp=subprocess.run(['/usr/bin/python3',str(root/'run_case.py'),'--scenario',scenario,'--case-id',cid,'--out-dir',str(out/cid),'--external-writer',str(root/'external_writer.py')],capture_output=True,text=True)
        row={'index':i,'case_id':cid,'scenario':scenario,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}
        rpath=out/cid/'result.json'
        if rpath.exists(): row['result']=json.loads(rpath.read_text())
        ledger.append(row)
        (out/'ledger.json').write_text(json.dumps(ledger,indent=2,sort_keys=True)+'\n')
        if cp.returncode!=0:
            print(json.dumps(row,indent=2,sort_keys=True)); return 2
    print(json.dumps({'completed':len(ledger),'out':str(out)},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
