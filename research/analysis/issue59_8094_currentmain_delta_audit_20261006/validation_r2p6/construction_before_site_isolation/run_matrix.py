"""One bounded engineering comparison; retains every subprocess result."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from fixture import build, corpus

ROOT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    freeze = json.loads((ROOT/'FREEZE.json').read_bytes())
    for name, sha in freeze['sha256'].items():
        if digest(ROOT/name) != sha:
            raise RuntimeError('SOURCE_CHANGED '+name)
    out = ROOT/'matrix'; out.mkdir(exist_ok=False)
    repo, baseline = build(out)
    cases = corpus(baseline)
    (out/'CASES.json').write_text(json.dumps(cases,indent=2)+'\n')
    records = []
    for i, case in enumerate(cases):
        for version, source in (('v1',ROOT/'original/verify.py'),('v2',ROOT/'verify_v2.py')):
            for optimized in (False,True):
                name = f'{i:02}-{case["name"]}-{version}-'+('optimized' if optimized else 'normal')
                folder = out/name; folder.mkdir()
                subject = folder/'subject.py'; shutil.copyfile(source,subject)
                payload = folder/'RESULT.json'; payload.write_text(case['input'])
                cmd = [sys.executable,'-I','-B']+(['-O'] if optimized else [])+[str(subject),'--repo',str(repo),'--result',str(payload)]
                start = time.time_ns()
                with (folder/'stdout.txt').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
                    proc = subprocess.Popen(cmd,stdout=stdout,stderr=stderr,cwd=ROOT)
                    try:
                        code = proc.wait(timeout=5); timeout = False
                    except subprocess.TimeoutExpired:
                        proc.kill();code=proc.wait();timeout=True
                row = dict(name=name,case=case['name'],version=version,optimized=optimized,
                           argv=cmd,pid=proc.pid,returncode=code,timeout=timeout,
                           started_wall_ns=start,finished_wall_ns=time.time_ns(),
                           input_sha256=digest(payload),source_sha256=digest(subject),
                           stdout_sha256=digest(folder/'stdout.txt'),stderr_sha256=digest(folder/'stderr.txt'))
                (folder/'execution.json').write_text(json.dumps(row,indent=2)+'\n')
                records.append(row)
                (out/'records.json').write_text(json.dumps(records,indent=2)+'\n')
                print(name,code,flush=True)
                if timeout:
                    (out/'STOP.json').write_text(json.dumps({'case':name,'reason':'CHILD_TIMEOUT'})+'\n')
                    return 2
    for name, sha in freeze['sha256'].items():
        if digest(ROOT/name) != sha:
            raise RuntimeError('SOURCE_CHANGED_AFTER_RUN '+name)
    (out/'END.json').write_text(json.dumps({'records':len(records),'source_unchanged':True,'returncode':0})+'\n')
    return 0
if __name__=='__main__':raise SystemExit(main())
