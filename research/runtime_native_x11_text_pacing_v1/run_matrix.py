#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ARMS=[(0,':310'),(12,':311'),(1,':312')]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--controller',type=Path,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for ms,disp in ARMS:
        arm=a.out/f'{ms:02d}ms'
        cp=subprocess.run([sys.executable,str(HERE/'run_arm.py'),'--out',str(arm),'--display',disp,'--pacing-ms',str(ms),'--controller',str(a.controller)],text=True,capture_output=True)
        (a.out/f'{ms:02d}ms.outer.stdout').write_text(cp.stdout); (a.out/f'{ms:02d}ms.outer.stderr').write_text(cp.stderr); (a.out/f'{ms:02d}ms.outer.exitcode').write_text(str(cp.returncode)+'\n')
        receipts.append({'pacing_ms':ms,'display':disp,'outer_exitcode':cp.returncode,'report_exists':(arm/'report.json').is_file()})
    (a.out/'matrix-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    agg=subprocess.run([sys.executable,str(HERE/'aggregate.py'),'--root',str(a.out),'--out',str(a.out/'aggregate.json')],text=True,capture_output=True)
    (a.out/'aggregate.stdout').write_text(agg.stdout); (a.out/'aggregate.stderr').write_text(agg.stderr); (a.out/'aggregate.exitcode').write_text(str(agg.returncode)+'\n')
    print(agg.stdout,end=''); return agg.returncode
if __name__=='__main__': raise SystemExit(main())
