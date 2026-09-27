"""Nine serial first-outcome workers; each actual process exit is retained."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()+b'\n'
def main(out):
    freeze=json.loads((ROOT/'FREEZE.json').read_bytes())
    for n,h in freeze['sources'].items():
        if sha((ROOT/n).read_bytes())!=h:raise ValueError('SOURCE_MISMATCH:'+n)
    out.mkdir(exist_ok=False,parents=True);(out/'CONSUMED').write_text(sha((ROOT/'FREEZE.json').read_bytes())+'\n')
    rows=[]
    for r in range(3):
        counts=[128,1024,8192];counts=counts[r:]+counts[:r]
        for n in counts:
            cid=f'n{n}-r{r}';d=out/cid
            cmd=[sys.executable,'-B',str(ROOT/'worker.py'),str(n),'1048576',str(r),str(d)]
            start=time.perf_counter_ns();p=subprocess.run(cmd,capture_output=True,timeout=10,cwd=ROOT)
            d.mkdir(exist_ok=True);(d/'stdout.json').write_bytes(p.stdout);(d/'stderr.txt').write_bytes(p.stderr)
            row={'id':cid,'n':n,'rep':r,'command':cmd,'returncode':p.returncode,'start_ns':start,'end_ns':time.perf_counter_ns(),'stdout_sha256':sha(p.stdout),'stderr_sha256':sha(p.stderr)}
            (d/'PROCESS.json').write_bytes(enc(row));rows.append(row)
            if p.returncode or p.stderr:raise RuntimeError('WORKER_FAILED:'+cid)
            raw=json.loads(p.stdout)
            if raw['n']!=n or raw['rep']!=r:raise RuntimeError('IDENTITY_MISMATCH')
    (out/'RUN.json').write_bytes(enc({'freeze_sha256':sha((ROOT/'FREEZE.json').read_bytes()),'rows':rows}));print('COMPLETE_9_CASES')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
