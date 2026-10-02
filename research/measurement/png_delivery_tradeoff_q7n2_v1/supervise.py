"""One synchronous bounded block with an observed external exit receipt."""
import json, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
index=int(sys.argv[1]); expected=sys.argv[2]
out=ROOT/'formal'/f'block-{index}'
if out.exists(): raise SystemExit('consumed output; refusing rerun')
command=[sys.executable,'-B',str(ROOT/'study.py'),'block',str(index),expected]
start=time.monotonic_ns()
try:
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=30)
    record={'command':command,'start_ns':start,'end_ns':time.monotonic_ns(),
            'returncode':result.returncode,'timeout':False,
            'stdout':result.stdout.decode(),'stderr':result.stderr.decode()}
except subprocess.TimeoutExpired as exc:
    record={'command':command,'start_ns':start,'end_ns':time.monotonic_ns(),
            'returncode':None,'timeout':True,
            'stdout':(exc.stdout or b'').decode(),'stderr':(exc.stderr or b'').decode()}
out.mkdir(parents=True,exist_ok=True)
(out/'OUTER.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps(record,sort_keys=True))
raise SystemExit(0 if record['returncode']==0 and not record['timeout'] else 1)
