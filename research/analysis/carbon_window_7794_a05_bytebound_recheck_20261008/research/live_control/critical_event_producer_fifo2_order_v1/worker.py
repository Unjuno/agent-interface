import argparse, json, pathlib, sqlite3, time
from model import digest, producer_offer
p=argparse.ArgumentParser(); p.add_argument('db'); p.add_argument('seq',type=int); p.add_argument('go'); p.add_argument('out'); a=p.parse_args()
go=pathlib.Path(a.go); out=pathlib.Path(a.out)
while not go.exists(): time.sleep(0.002)
c=sqlite3.connect(a.db,isolation_level=None,timeout=5.0)
t0=time.monotonic_ns(); c.execute('BEGIN IMMEDIATE'); t1=time.monotonic_ns()
st=producer_offer(c,2,a.seq,f'E{a.seq}',digest(f'p{a.seq}')); c.execute('COMMIT'); t2=time.monotonic_ns(); c.close()
out.write_text(json.dumps({'seq':a.seq,'status':st,'begin_request_ns':t0,'begin_acquired_ns':t1,'commit_ns':t2},sort_keys=True)+'\n')
