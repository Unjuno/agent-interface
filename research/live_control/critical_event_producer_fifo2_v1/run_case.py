import argparse,sqlite3,subprocess,os,time,json,pathlib,signal
from model import *
p=argparse.ArgumentParser(); p.add_argument('--policy',choices=['single','fifo2']); p.add_argument('--id'); p.add_argument('--out'); a=p.parse_args()
out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False); db=str(out/'state.db'); ready=str(out/'ready')
init_db(db); cap=1 if a.policy=='single' else 2
pr=subprocess.Popen(['python3',str(pathlib.Path(__file__).with_name('worker.py')),db,str(cap),ready])
for _ in range(200):
    if os.path.exists(ready): break
    time.sleep(.01)
else: raise RuntimeError('no ready')
os.kill(pr.pid,signal.SIGKILL); rc=pr.wait()
postkill=snap(db)
c=sqlite3.connect(db,isolation_level=None)
controls={}
if a.policy=='fifo2':
    controls['e6']=producer_offer(c,cap,6,'E6',digest('p6'))
    controls['e5_early']=pending_retry(c,5,'E5',digest('p5'))
else:
    controls['e5_offer_after_restart']=producer_offer(c,cap,5,'E5',digest('p5'))
ack_sha=ack_digest(c,2)
c.execute('BEGIN IMMEDIATE'); controls['ack1']=ack_through(c,2,ack_sha); c.execute('COMMIT')
c.execute('BEGIN IMMEDIATE'); controls['ack_replay']=ack_through(c,2,ack_sha); c.execute('ROLLBACK')
statuses=[]
for i in (4,5):
    c.execute('BEGIN IMMEDIATE'); st=pending_retry(c,i,f'E{i}',digest(f'p{i}'))
    if st=='EVENT_ACCEPTED': c.execute('COMMIT')
    else: c.execute('ROLLBACK')
    statuses.append(st)
c.close(); final=snap(db)
probe=subprocess.run(['python3','-c','import sys;sys.path.insert(0,sys.argv[2]);from model import snap;import json;print(json.dumps(snap(sys.argv[1]),sort_keys=True))',db,str(pathlib.Path(__file__).parent)],capture_output=True,text=True,check=True)
restart=json.loads(probe.stdout)
res={'id':a.id,'policy':a.policy,'kill_rc':rc,'postkill':postkill,'controls':controls,'drain':statuses,'final':final,'restart':restart}
(out/'result.json').write_text(json.dumps(res,sort_keys=True,indent=2)+'\n'); print(json.dumps(res,sort_keys=True))
