import json,sys,datetime
from pathlib import Path
def load(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
pressure=load(sys.argv[1]); control=load(sys.argv[2])
assert any(r.get('event')=='pressure_ready' and r.get('allocated_mib')==640 for r in pressure),'false success / target missing'
def avail(r):
 try:return int(r['meminfo']['MemAvailable'].split()[0])
 except:return 10**12
assert min(avail(r) for r in pressure)<128*1024,'pressure not independently evidenced'
labels=[r['label'] for r in control]
required=['session-info','sessions','list-before','stats','logs','stop','list-after-stop','inspect','remove','list-after-remove']
for k in required: assert labels.count(k)==1,'missing/duplicate control op: '+k
for r in control:
 assert r['exit']==0 and r['elapsed_ms']<=15000,'control failure/deadline: '+r['label']
def obj(r):
 try:return json.loads(r['output'])
 except:return None
stop=next(r for r in control if r['label']=='stop')
after=next(r for r in control if r['label']=='list-after-stop')
assert 'Exited (137)' in after['output'] or 'State":"exited' in after['output'],'stop acknowledgement lacks exited state'
removed=next(r for r in control if r['label']=='list-after-remove')
assert removed['output'].strip()=='','cleanup absence not independently confirmed'
ts=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
ready=next(r for r in pressure if r.get('event')=='pressure_ready')
first=ts(control[0]['ts']); tready=ts(ready['ts'])
assert 0 <= (first-tready).total_seconds() <= 60,'controls not timestamp-overlapped with pressure hold'
print(json.dumps({'audit':'PASS','pressure_memavailable_min_kib':min(avail(r) for r in pressure),'controls':len(control),'stop_elapsed_ms':stop['elapsed_ms'],'stop_state':'Exited (137)','overlap_seconds':(first-tready).total_seconds()}))
