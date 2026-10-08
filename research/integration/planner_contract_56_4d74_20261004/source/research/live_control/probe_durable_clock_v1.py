"""Injected split clock replies; new command blocked until own valid clock resolves."""
import copy,hashlib,json
from pathlib import Path
from durable_submit_v3 import initialize,run
HERE=Path(__file__).resolve().parent
root=HERE/'results/durable-clock-01';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2)+'\n')
dump('plan.json',{'scope':'injected transport, not a real socket or latency result','sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['probe_durable_clock_v1.py','durable_submit_v3.py','received_continuation_v1.py']}})
c=json.loads((HERE/'results/durable-replan-01/recovered.json').read_text())['continuation']
p=root/'journal.json';initialize(p,c);calls=[]
def transport(records):
 def reply(socket,q,**kwargs):
  calls.append(q);dump('requests.json',calls)
  return {'status':'timeout','cursor':q['after']+len(records),'records':copy.deepcopy(records)}
 return reply
# An old orphan clock cannot resolve this newly requested clock.
first=run(p,{'command':{'op':'clock'},'timeout':0},transport([{'event':'clock','runtime_ns':1,'sequence':c['observation']['sequence']}]))
assert first['state']['pending'] is not None
dump('orphan-clock.json',first)
rid=first['request']['request_id'];assert 'action_id' not in first['request']
before=p.read_bytes()
for command in ({'op':'clock'},{'op':'submit','steps':[{'op':'observe'}]}):
 try:run(p,{'command':command,'timeout':0},transport([]))
 except ValueError as e:assert str(e)=='unresolved command; read only'
 else:raise AssertionError('new command escaped pending lock')
assert len(calls)==1 and p.read_bytes()==before
second=run(p,{'timeout':0},transport([{'event':'command','command':{'op':'clock','transport_request_id':rid}}]))
assert second['state']['pending']['echo_seen'] and second['state']['pending'] is not None
dump('echo-only.json',second)
third=run(p,{'timeout':0},transport([]));assert third['state']['pending'] is not None
dump('empty-timeout.json',third)
before=p.read_bytes()
try:run(p,{'timeout':0},transport([{'event':'clock','runtime_ns':-1,'sequence':c['observation']['sequence']}]))
except ValueError as e:assert str(e)=='invalid clock'
else:raise AssertionError('malformed clock escaped validation')
assert p.read_bytes()==before
final=run(p,{'timeout':0},transport([{'event':'clock','runtime_ns':100,'sequence':c['observation']['sequence']}]))
assert final['state']['pending'] is None and final['state']['last_resolution']['request_id']==rid
assert final['state']['last_resolution']['clock']['runtime_ns']==100
assert final['state']['continuation']['clocks'][rid]['record']==final['state']['last_resolution']['clock']
assert final['state']['continuation']['observation']==c['observation']
assert sum('command' in q for q in calls)==1 and all('action_id' not in q for q in calls)
dump('resolved.json',final)
dump('result.json',{'network_calls':0,'injected_calls':len(calls),'clock_commands':1,'blocked_new_commands':2,'orphan_clock_ignored':True,'echo_and_timeout_remain_pending':True,'malformed_clock_preserved_checkpoint':True,'own_clock_resolved':True,'observation_retained':True})
print((root/'result.json').read_text())
