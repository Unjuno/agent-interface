#!/usr/bin/env python3
import json,subprocess,sys,time
from pathlib import Path
STUDY=Path(__file__).resolve().parent
SC=['STABLE_UP','DISCONNECT_PRESS','DISCONNECT_RELEASE','RECONNECTED_PRESS_RELEASE','NO_BOOTSTRAP','WRONG_EPOCH_BOOTSTRAP']
POL=['CARRY_OLD_STATE','REBOOTSTRAP_ON_RECONNECT']
def schedule():
    rows=[]
    for rep in range(2):
      for s in SC:
        for p in POL: rows.append((s,p,rep))
    return rows
def main():
    idx=int(sys.argv[1]); root=Path(sys.argv[2]); marker=root/f'batch{idx}.consumed'
    if idx not in range(6): raise SystemExit('bad batch')
    if marker.exists(): raise SystemExit('batch consumed')
    if idx and not (root/f'batch{idx-1}_outer_rc').exists(): raise SystemExit('previous external exit absent')
    if idx and (root/f'batch{idx-1}_outer_rc').read_text().strip()!='0': raise SystemExit('previous external exit nonzero')
    marker.parent.mkdir(parents=True,exist_ok=True); marker.write_text(str(time.time_ns()))
    rows=schedule()[idx*4:(idx+1)*4]; receipts=[]
    for j,(s,p,r) in enumerate(rows):
        out=root/f'case{idx*4+j:02d}_{s}_{p}_r{r}'
        q=subprocess.run([sys.executable,'-B',str(STUDY/'run_case.py'),s,p,str(r),str(out)],capture_output=True,text=True,timeout=12)
        receipts.append({'case':idx*4+j,'scenario':s,'policy':p,'rep':r,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
        if q.returncode: break
    (root/f'batch{idx}_receipt.json').write_text(json.dumps(receipts,indent=2,sort_keys=True))
    if len(receipts)!=len(rows) or any(x['returncode'] for x in receipts): raise SystemExit(2)
    print(json.dumps({'status':'BATCH_DONE','batch':idx,'cases':len(rows)},sort_keys=True))
if __name__=='__main__':main()
