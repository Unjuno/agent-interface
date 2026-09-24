"""One bounded synchronous batch. No hidden retry, detached work or overwrite."""
import json, subprocess, sys, time
from pathlib import Path
root=Path(__file__).resolve().parent
phase,index=sys.argv[1],int(sys.argv[2]);dest=root/phase/('b'+str(index))
if dest.exists():raise SystemExit('refuse existing allocation')
start=time.monotonic_ns()
try:
    p=subprocess.run([sys.executable,'-S','-B',str(root/'run.py'),phase,str(index)],capture_output=True,timeout=30)
    rc=p.returncode;stdout=p.stdout;stderr=p.stderr
except subprocess.TimeoutExpired as e:
    rc=None;stdout=e.stdout or b'';stderr=e.stderr or b''
dest.mkdir(parents=True,exist_ok=True)
(dest/'launcher.stdout').write_bytes(stdout);(dest/'launcher.stderr').write_bytes(stderr)
(dest/'launcher.json').write_text(json.dumps({'start_ns':start,'end_ns':time.monotonic_ns(),'exit':rc},sort_keys=True)+'\n')
print(json.dumps({'phase':phase,'batch':index,'exit':rc}))
raise SystemExit(rc if rc is not None else 124)
