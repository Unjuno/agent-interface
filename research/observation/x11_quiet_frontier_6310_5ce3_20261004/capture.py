"""Exclusive command receipt; preparation/validation only."""
import datetime,json,subprocess,sys,time
from pathlib import Path
destination=Path(sys.argv[1]);command=sys.argv[2:]
destination.parent.mkdir(parents=True,exist_ok=True)
with destination.open('x') as f:
    start=time.monotonic_ns();utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        p=subprocess.run(command,capture_output=True,timeout=120)
        result={'returncode':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')}
    except subprocess.TimeoutExpired as e:
        result={'returncode':None,'error':'COMMAND_TIMEOUT','stdout':(e.stdout or b'').decode(errors='replace'),'stderr':(e.stderr or b'').decode(errors='replace')}
    result.update(command=command,started_utc=utc,elapsed_ns=time.monotonic_ns()-start)
    json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'receipt':str(destination),'returncode':result['returncode'],'tail':result['stderr'][-1500:]}))
raise SystemExit(0 if result['returncode']==0 else 1)
