"""Execute one unique case and retain real child exit; no old allocation reruns."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    phase,index=sys.argv[1],int(sys.argv[2])
    if phase=='formal':
        specs=json.loads((HERE/'SCHEDULE.json').read_text())
        for name,want in json.loads((HERE/'FREEZE.json').read_text())['files'].items():
            if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=want: raise SystemExit('SOURCE_CHANGED:'+name)
        if not 0<=index<len(specs): raise SystemExit('BAD_INDEX')
        spec=specs[index]
        for earlier in range(index):
            prev=HERE/'data'/'formal'/f'case{earlier:02d}'/'PROCESS.json'
            if not prev.exists() or json.loads(prev.read_text())['exit']!=0: raise SystemExit('PRIOR_CASE_NOT_COMPLETE')
    elif phase=='construction':
        spec={'id':'construction-'+str(index),'rep':-1,'first':[[2,1],[8,4]][index]}
    else:raise SystemExit('BAD_PHASE')
    spec=dict(spec,phase=phase)
    out=HERE/'data'/phase/f'case{index:02d}';out.mkdir(parents=True,exist_ok=False)
    args=[sys.executable,'-B',str(HERE/'worker.py'),str(out/'raw'),json.dumps(spec,sort_keys=True)]
    rec={'argv':args,'spec':spec,'supervisor_pid':os.getpid(),'start_ns':time.monotonic_ns(),'timeout':False}
    with (out/'stdout.txt').open('wb') as so,(out/'stderr.txt').open('wb') as se:
        p=subprocess.Popen(args,stdout=so,stderr=se,start_new_session=True);rec['worker_pid']=p.pid
        try:rec['exit']=p.wait(timeout=25)
        except subprocess.TimeoutExpired:
            rec['timeout']=True;os.killpg(p.pid,signal.SIGTERM)
            try:rec['exit']=p.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rec['exit']=p.wait(timeout=2)
    rec['end_ns']=time.monotonic_ns()
    (out/'PROCESS.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
    print(json.dumps(rec,sort_keys=True));print((out/'stdout.txt').read_text())
    return 0 if rec['exit']==0 and not rec['timeout'] else 2
if __name__=='__main__':raise SystemExit(main())
