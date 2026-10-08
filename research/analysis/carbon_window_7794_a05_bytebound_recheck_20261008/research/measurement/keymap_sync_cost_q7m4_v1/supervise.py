"""Synchronous one-shot outer receipt; refuse consumed output and missing predecessor."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    root=Path(sys.argv[1]);rep=int(sys.argv[2]);root.mkdir(exist_ok=True)
    if not 0<=rep<5:raise ValueError('rep bounds')
    if rep:
        prev=json.loads((root/f'batch{rep-1}.exit.json').read_text())
        if prev['returncode']!=0:raise ValueError('predecessor failed')
    marker=root/f'batch{rep}.consumed';marker.open('x').close()
    cmd=[sys.executable,'-B',str(HERE/'run.py'),str(root/f'batch{rep}'),str(rep),'32'];start=time.monotonic_ns()
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=p.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGTERM)
        try:out,err=p.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate()
        err+=b'\nOUTER_TIMEOUT\n'
    (root/f'batch{rep}.stdout').write_bytes(out);(root/f'batch{rep}.stderr').write_bytes(err)
    x=dict(argv=cmd,pid=p.pid,before_ns=start,after_ns=time.monotonic_ns(),returncode=p.returncode,stdout_sha256=hashlib.sha256(out).hexdigest(),stderr_sha256=hashlib.sha256(err).hexdigest())
    (root/f'batch{rep}.exit.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
    print(json.dumps(x,sort_keys=True));sys.exit(0 if p.returncode==0 and not err else 1)
