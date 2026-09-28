import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from run_case import CASES

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--batch',type=int,choices=[0,1],required=True); a=ap.parse_args()
    root=Path(a.out); root.mkdir(parents=True,exist_ok=False)
    chosen=CASES[a.batch*9:(a.batch+1)*9]
    rows=[]
    for idx,name in enumerate(chosen):
        cdir=root/f'{idx+a.batch*9:02d}-{name}'
        p=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('run_case.py')),'--case',name,'--out',str(cdir)],capture_output=True,text=True,timeout=10)
        rows.append({'case':name,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'result_sha256':sha(cdir/'result.json') if (cdir/'result.json').exists() else None})
        if p.returncode!=0: break
    rec={'batch':a.batch,'planned':chosen,'rows':rows,'complete':len(rows)==len(chosen) and all(r['returncode']==0 for r in rows),'created_ns':time.monotonic_ns()}
    (root/'batch_receipt.json').write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'batch':a.batch,'rows':len(rows),'complete':rec['complete']}))
    raise SystemExit(0 if rec['complete'] else 2)
if __name__=='__main__': main()
