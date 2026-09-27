"""Bounded foreground supervisor; records an actual wait status, never an inferred one."""
import json,os,signal,subprocess,sys,time
from pathlib import Path
here=Path(__file__).resolve().parent
out=Path(sys.argv[2]).resolve(); receipt=out.with_suffix('.execution.json')
if out.exists() or receipt.exists(): raise SystemExit('REFUSE_CONSUMED_PATH')
cmd=[sys.executable,'-B',str(here/'runner.py'),*sys.argv[1:]]
start=time.monotonic_ns(); timed_out=False
with out.with_suffix('.stdout').open('x') as stdout, out.with_suffix('.stderr').open('x') as stderr:
    p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,start_new_session=True)
    try: code=p.wait(timeout=35)
    except subprocess.TimeoutExpired:
        timed_out=True; os.killpg(p.pid,signal.SIGTERM)
        try: code=p.wait(timeout=3)
        except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL); code=p.wait(timeout=2)
rec={'cmd':cmd,'child_pid':p.pid,'returncode':code,'timed_out':timed_out,'started_ns':start,'ended_ns':time.monotonic_ns()}
receipt.write_text(json.dumps(rec,sort_keys=True)+'\n'); print(json.dumps(rec)); sys.exit(int(code!=0 or timed_out))
