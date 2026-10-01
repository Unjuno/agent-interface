from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

TIERS = [1048576, 16777216, 262144, 4194304]
THREAD_ENV = {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'}

def main(root: Path, outdir: Path):
    root=Path(root); outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=False)
    invocation={'formal_invocations':1,'started_ns':time.time_ns(),'tier_order':TIERS,'thread_env':THREAD_ENV}
    (outdir/'INVOCATION.json').write_text(json.dumps(invocation,sort_keys=True,indent=2)+'\n')
    rows=[]
    for i,n in enumerate(TIERS):
        env=os.environ.copy(); env.update(THREAD_ENV)
        p=outdir/f'tier_{i}_{n}.json'
        cp=subprocess.run([sys.executable,str(root/'src/tier_worker.py'),str(n),str(p)],env=env,cwd=root,
                          text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=False)
        (outdir/f'tier_{i}_{n}.stdout').write_text(cp.stdout)
        (outdir/f'tier_{i}_{n}.stderr').write_text(cp.stderr)
        if cp.returncode!=0:
            raise SystemExit(f'tier_failed:{n}:rc={cp.returncode}')
        row=json.loads(p.read_text()); row['tier_order_index']=i; rows.append(row)
    (outdir/'formal_rows.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'tiers':[r['parameter_count'] for r in rows]}))
if __name__=='__main__': main(Path(sys.argv[1]),Path(sys.argv[2]))
