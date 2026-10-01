#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEP=HERE.parent/'runtime_native_x11_text_pacing_v1'
RUN_ARM=DEP/'run_arm.py'
SCHEDULE=[[0.8,0.9,1.0,1.1],[1.1,1.0,0.9,0.8],[0.9,1.1,0.8,1.0],[1.0,0.8,1.1,0.9],[1.1,0.9,1.0,0.8]]
def key(ms): return f'{int(round(ms*1000)):04d}us'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--controller',type=Path,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    receipts=[]; display_no=350
    for rnd,order in enumerate(SCHEDULE,1):
        for ms in order:
            arm=a.out/f'r{rnd:02d}'/key(ms); disp=f':{display_no}'; display_no+=1
            cp=subprocess.run([sys.executable,str(RUN_ARM),'--out',str(arm),'--display',disp,'--pacing-ms',str(ms),'--controller',str(a.controller)],text=True,capture_output=True)
            arm.parent.mkdir(parents=True,exist_ok=True)
            (arm.parent/f'{key(ms)}.outer.stdout').write_text(cp.stdout); (arm.parent/f'{key(ms)}.outer.stderr').write_text(cp.stderr); (arm.parent/f'{key(ms)}.outer.exitcode').write_text(str(cp.returncode)+'\n')
            receipts.append({'round':rnd,'pacing_ms':ms,'display':disp,'outer_exitcode':cp.returncode,'report_exists':(arm/'report.json').is_file()})
    (a.out/'schedule-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    agg=subprocess.run([sys.executable,str(HERE/'aggregate.py'),'--root',str(a.out),'--out',str(a.out/'aggregate.json')],text=True,capture_output=True)
    (a.out/'aggregate.stdout').write_text(agg.stdout); (a.out/'aggregate.stderr').write_text(agg.stderr); (a.out/'aggregate.exitcode').write_text(str(agg.returncode)+'\n')
    print(agg.stdout,end=''); return agg.returncode
if __name__=='__main__': raise SystemExit(main())
