import json, os, sys, time
from pathlib import Path
case=Path(__file__).resolve().parent/sys.argv[1]
index=int(sys.argv[2]); request=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8-sig'))
helper_started_ns=time.monotonic_ns();helper_started_utc_ns=time.time_ns()
path=case/'commands'/f'{index:03d}.json'
if path.exists(): raise RuntimeError('command already allocated; inspect original reply instead')
tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(request)+'\n'); tmp.rename(path)
published_ns=time.monotonic_ns();published_utc_ns=time.time_ns()
reply=case/'replies'/path.name
for _ in range(250):
    if reply.exists():
        row=json.loads(reply.read_text())
        received_ns=time.monotonic_ns();received_utc_ns=time.time_ns()
        timing=case/'command-timing';timing.mkdir(exist_ok=True)
        (timing/path.name).write_text(json.dumps({'helper_started_ns':helper_started_ns,'helper_started_utc_ns':helper_started_utc_ns,'published_ns':published_ns,'published_utc_ns':published_utc_ns,'reply_read_ns':received_ns,'reply_read_utc_ns':received_utc_ns,'owner_accepted_ns':row['started_ns'],'owner_result_ready_ns':row['ended_ns'],'scope':'Execution host clock; reply readiness/read not primary image ingestion or semantic awareness'},indent=2)+'\n')
        if isinstance(row.get('reply'),dict) and isinstance(row['reply'].get('image'),dict):row['reply']['image']['data']='[original bytes retained in reply file; view image artifact separately]'
        print(json.dumps(row)); break
    if (case/'exception.json').exists(): print((case/'exception.json').read_text()); sys.exit(1)
    time.sleep(.02)
else: print('REPLY_PENDING: inspect original command/reply; do not reissue')
