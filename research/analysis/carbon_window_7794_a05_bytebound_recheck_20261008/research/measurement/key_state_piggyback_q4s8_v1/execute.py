"""One synchronous context batch; writes actual runner exit, never reruns it."""
from pathlib import Path
import json,os,signal,subprocess,sys,time
HERE=Path(__file__).resolve().parent
CONTEXTS=('UP','DOWN','EDGE_BURST','FOCUS_RETURN')
def main(root,context,formal):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    if context not in CONTEXTS:raise ValueError('unknown context')
    if formal:
        for previous in CONTEXTS[:CONTEXTS.index(context)]:
            p=json.loads((root/(previous+'.process.json')).read_bytes())
            if p['returncode']!=0 or p['timeout']:raise RuntimeError('prior batch incomplete')
    with (root/(context+'.consumed')).open('x') as f:f.write('single invocation\n')
    argv=[sys.executable,'-B',str(HERE/'run.py'),str(root/context),context,'formal' if formal else 'construct']
    t=time.monotonic_ns();timeout=False
    p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:stdout,stderr=p.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        timeout=True;os.killpg(p.pid,signal.SIGTERM)
        try:stdout,stderr=p.communicate(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate(timeout=3)
    (root/(context+'.stdout')).write_bytes(stdout);(root/(context+'.stderr')).write_bytes(stderr)
    (root/(context+'.process.json')).write_text(json.dumps(dict(argv=argv,pid=p.pid,start_ns=t,end_ns=time.monotonic_ns(),returncode=p.returncode,timeout=timeout),sort_keys=True)+'\n')
    return p.returncode if not timeout else 124
if __name__=='__main__':sys.exit(main(sys.argv[1],sys.argv[2],sys.argv[3]=='formal'))
