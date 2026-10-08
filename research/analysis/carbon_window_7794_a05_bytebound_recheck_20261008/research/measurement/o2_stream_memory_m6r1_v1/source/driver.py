"""Bounded sequential process receipts; no retry and no evaluation in imports."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')

def main(index):
    root=ROOT/'receipts';root.mkdir(exist_ok=True)
    receipt=root/f'{index:02d}.json'
    if receipt.exists() or (ROOT/'formal'/f'{index:02d}').exists():raise SystemExit('condition already consumed')
    if index and not (root/f'{index-1:02d}.json').exists():raise SystemExit('missing previous condition')
    if index and json.loads((root/f'{index-1:02d}.json').read_text()).get('returncode')!=0:raise SystemExit('previous condition incomplete')
    argv=[sys.executable,'-B',str(ROOT/'source/run_case.py'),str(index)]
    row=dict(index=index,argv=argv,start_ns=time.monotonic_ns(),status='STARTED')
    save(receipt,row)
    with (root/f'{index:02d}.stdout').open('xb') as stdout,(root/f'{index:02d}.stderr').open('xb') as stderr:
        p=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
        row['pid']=p.pid;save(receipt,row)
        try: rc=p.wait(timeout=40)
        except subprocess.TimeoutExpired:
            p.kill();rc=p.wait();row['timeout']=True
    row.update(returncode=rc,end_ns=time.monotonic_ns(),status='TERMINAL')
    for ext in ('stdout','stderr'):
        row[ext+'_sha256']=hashlib.sha256((root/f'{index:02d}.{ext}').read_bytes()).hexdigest()
    save(receipt,row);print(json.dumps(row));return rc

if __name__=='__main__':sys.exit(main(int(sys.argv[1])))
