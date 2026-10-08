from pathlib import Path
import json,shutil,hashlib
r=Path(__file__).resolve().parent;old=r/'relay-construction-01';f=json.loads((old/'FREEZE.json').read_text());snap=old/'source-snapshot';snap.mkdir(exist_ok=False)
for name,h in f['files'].items():
 data=(r/name).read_bytes();assert hashlib.sha256(data).hexdigest()==h;t=snap/name;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(data)
print({'late_readable_request_5_bytes':len((old/'request-000005.jsonl').read_bytes()),'original_source_snapshot_members':len(f['files'])})
s=(r/'run_relay_construction.py').read_text().replace("relay-construction-01'","relay-construction-02'").replace("construction01'","construction02'").replace("'run_relay_construction.py'","'run_relay_construction_02.py'")
s=s.replace('req=0;resp=0;start=time.monotonic()','req=0;resp=0;start=time.monotonic(); sharing_wait=[];blocked_since=None')
s=s.replace("b=p.read_bytes();json.loads(b);host.stdin.write(b);host.stdin.flush();req+=1",'''try:
                b=p.read_bytes()
            except PermissionError as problem:
                now=time.monotonic()
                if blocked_since is None:blocked_since=now
                sharing_wait.append({'request_index':req,'observed_s':now-start,'error':repr(problem)})
                if now-blocked_since>2:raise TimeoutError('request sharing unavailable >2s') from problem
                time.sleep(.01);continue
            blocked_since=None
            json.loads(b);host.stdin.write(b);host.stdin.flush();req+=1''')
s=s.replace("'input_emissions':0}","'input_emissions':0,'sharing_waits':sharing_wait}")
s=s.replace("error=repr(e)","error=repr(e)\n    import traceback\n    (out/'exception.txt').write_text(traceback.format_exc())")
(r/'run_relay_construction_02.py').write_text(s)
