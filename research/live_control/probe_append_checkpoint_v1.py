"""Damage/capacity and pre-send-sync failure controls for append checkpoint candidate."""
import hashlib,json,os
from pathlib import Path
import append_checkpoint_v1 as storage
from durable_submit_v4 import initialize,run
from received_continuation_v1 import start
HERE=Path(__file__).resolve().parent
root=HERE/'results/append-checkpoint-01';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2)+'\n')
dump('plan.json',{'scope':'file damage and injected fsync failure; no real socket or power-loss claim','sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['probe_append_checkpoint_v1.py','append_checkpoint_v1.py','durable_submit_v4.py']}})
p=root/'base.jsonl';initialize(p,start('synthetic-session'))
initial=storage.load(p);pending=dict(initial,pending={'test':'uncertain'});storage.store(p,pending)
raw=p.read_bytes();assert storage.load(p)==pending and storage.inspect(p)[1]==2
controls={};calls=[]
def transport(*args,**kwargs):calls.append(args);raise AssertionError('transport forbidden')
variants={'partial_tail':raw[:-5], 'bad_json':raw+b'not-json\n', 'duplicate_frame':raw+raw.splitlines(keepends=True)[-1], 'changed_payload':raw.replace(b'uncertain',b'certainxx')}
for name,data in variants.items():
 q=root/(name+'.jsonl');q.write_bytes(data);before=q.read_bytes()
 try:run(q,{'command':{'op':'clock'},'timeout':0},transport)
 except (ValueError,TypeError,KeyError):pass
 else:raise AssertionError(name)
 assert q.read_bytes()==before;controls[name]='refused before transport, bytes unchanged'
q=root/'sync-failure.jsonl';initialize(q,start('synthetic-session'))
original=storage.os.fsync
try:
 def fail(fd):raise OSError('injected sync failure before any transport')
 storage.os.fsync=fail
 try:run(q,{'command':{'op':'clock'},'timeout':0},transport)
 except OSError as error:assert str(error).startswith('injected sync')
 else:raise AssertionError('sync error not propagated')
finally:storage.os.fsync=original
assert storage.load(q)['pending']['write_state']=='may_have_been_sent'
try:run(q,{'command':{'op':'clock'},'timeout':0},transport)
except ValueError as error:assert str(error)=='unresolved command; read only'
else:raise AssertionError('uncertainty cleared after failed sync')
controls['pre_send_sync_failure']='pending visible and next command blocked; physical durability unknown'
q=root/'capacity.jsonl';storage.store(q,{'small':1})
for i in range(255):storage.store(q,{'small':i})
before=q.read_bytes()
try:storage.store(q,{'small':256})
except ValueError as error:assert 'capacity' in str(error)
else:raise AssertionError('capacity unbounded')
assert q.read_bytes()==before and storage.inspect(q)[1]==256
controls['capacity']='256 records retained; next refused unchanged'
assert calls==[]
dump('result.json',{'controls':controls,'transport_calls':0,'scope':'controlled file damage/sync error, not power interruption; no automatic salvage'})
print((root/'result.json').read_text())
