#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEP=HERE.parent/'runtime_native_x11_text_pacing_v1'
RUN_ARM=DEP/'run_arm.py'
BATCHES={1:[0.8,0.9,1.0,1.1],2:[1.1,1.0,0.9,0.8],3:[0.9,1.1,0.8,1.0],4:[1.0,0.8,1.1,0.9],5:[1.1,0.9,1.0,0.8]}
def key(ms): return f'{int(round(ms*1000)):04d}us'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--batch',type=int,choices=range(1,6),required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--controller',type=Path,required=True); a=ap.parse_args()
    if a.out.exists(): raise SystemExit('batch output exists')
    a.out.mkdir(parents=True)
    rows=[]; display_no=370+(a.batch-1)*4
    for ms in BATCHES[a.batch]:
        arm=a.out/key(ms); disp=f':{display_no}'; display_no+=1
        cp=subprocess.run([sys.executable,str(RUN_ARM),'--out',str(arm),'--display',disp,'--pacing-ms',str(ms),'--controller',str(a.controller)],text=True,capture_output=True)
        (a.out/f'{key(ms)}.outer.stdout').write_text(cp.stdout); (a.out/f'{key(ms)}.outer.stderr').write_text(cp.stderr); (a.out/f'{key(ms)}.outer.exitcode').write_text(str(cp.returncode)+'\n')
        rows.append({'pacing_ms':ms,'display':disp,'outer_exitcode':cp.returncode,'report_exists':(arm/'report.json').is_file(),'score_exists':(arm/'score.json').is_file()})
    complete=all(r['report_exists'] and r['score_exists'] for r in rows)
    receipt={'schema':'agent-interface/native-x11-subms-robustness-batch-v2','batch':a.batch,'order':BATCHES[a.batch],'rows':rows,'complete':complete}
    (a.out/'batch-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps(receipt,indent=2)); return 0 if complete else 2
if __name__=='__main__': raise SystemExit(main())
