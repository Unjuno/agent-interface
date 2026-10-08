#!/usr/bin/env python3
import argparse,json,random,subprocess,sys,time
from pathlib import Path
SCENARIOS=['stable','switch_to_B','A_B_A','unrelated_pointer']; SEED=37120260916
sched=[s for s in SCENARIOS for _ in range(5)]; random.Random(SEED).shuffle(sched)
ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--run-case',required=True); ap.add_argument('--start',type=int,required=True); ap.add_argument('--stop',type=int,required=True); ap.add_argument('--display-base',type=int,default=180); a=ap.parse_args()
root=Path(a.root); root.mkdir(parents=True,exist_ok=True)
sp=root/'schedule.json'
expected={'seed':SEED,'ordered_scenarios':sched}
if sp.exists():
    if json.loads(sp.read_text())!=expected: raise SystemExit('schedule mismatch')
else: sp.write_text(json.dumps(expected,indent=2))
ledger=root/'ledger.jsonl'
seen=set()
if ledger.exists():
    for line in ledger.read_text().splitlines():
        if line.strip(): seen.add(json.loads(line)['index'])
for i in range(a.start,a.stop):
    if i in seen: raise SystemExit(f'index already completed: {i}')
    s=sched[i]; cid=f'{i:02d}-{s}'; out=root/cid
    if out.exists(): raise SystemExit(f'case dir already exists: {cid}')
    cmd=[sys.executable,a.run_case,'--scenario',s,'--out',str(out),'--display',str(a.display_base+i)]
    t=time.monotonic_ns(); cp=subprocess.run(cmd,text=True,capture_output=True); elapsed=time.monotonic_ns()-t
    row={'case_id':cid,'index':i,'scenario':s,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'elapsed_ns':elapsed}
    if cp.returncode==0: row['result']=json.loads((out/'result.json').read_text())
    with open(ledger,'a') as f: f.write(json.dumps(row,sort_keys=True)+'\n')
    print(cid,cp.returncode,flush=True)
    if cp.returncode!=0:
        (root/'STOPPED.json').write_text(json.dumps({'reason':'case_failure','case_id':cid,'row':row},indent=2)); raise SystemExit(2)
