"""Blocking one-shot parent with observed return code and owned-group cleanup."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    out=ROOT/'formal-01';marker=ROOT/'FORMAL_CONSUMED'
    with marker.open('x') as f:f.write(hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest()+'\n')
    if out.exists():raise RuntimeError('FORMAL_OUTPUT_OCCUPIED')
    cmd=[sys.executable,'-B',str(ROOT/'run.py'),str(out)]
    started=time.perf_counter_ns();p=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    timeout=False
    try:stdout,stderr=p.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        timeout=True;os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate(timeout=5)
    out.mkdir(exist_ok=True)
    (out/'runner.stdout').write_bytes(stdout);(out/'runner.stderr').write_bytes(stderr)
    record={'command':cmd,'pid':p.pid,'returncode':p.returncode,'timeout':timeout,'start_ns':started,'end_ns':time.perf_counter_ns(),'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()}
    (out/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));sys.exit(0 if p.returncode==0 and not timeout else 2)
