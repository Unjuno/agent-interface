import json,hashlib,shutil
from pathlib import Path
import append_checkpoint_v1 as old
import append_checkpoint_capacity_v2 as new
out=Path('/out');out.mkdir(exist_ok=True)
original=Path('/prior/formal-output/block-1/B/client/journal.jsonl');raw=original.read_bytes();state,count,previous,size=old.inspect(original)
assert count==256 and state['pending'] is not None
copy=out/'copied-journal.jsonl';copy.write_bytes(raw)
try:old.store(copy,state)
except ValueError as e:assert 'capacity exhausted' in str(e)
else:raise AssertionError('old limit unexpectedly accepted')
assert copy.read_bytes()==raw
new.store(copy,state);assert copy.read_bytes().startswith(raw) and new.inspect(copy)[1]==257
assert new.load(copy)['pending']==state['pending']
large=out/'large.jsonl'
try:new.store(large,{'payload':'x'*new.MAX_RECORD})
except ValueError:pass
else:raise AssertionError('frame bound lost')
assert not large.exists()
torn=out/'torn.jsonl';torn.write_bytes(raw[:-1])
try:new.load(torn)
except ValueError:pass
else:raise AssertionError('torn accepted')
bound=out/'bounded.jsonl';prev=None;lines=[]
for i in range(1,1025):
 record={'version':'append-checkpoint-v1','index':i,'previous':prev,'state':{'pending':None,'authority':'none'}}
 record['sha256']=hashlib.sha256(new.encoded(record)).hexdigest();prev=record['sha256'];lines.append(new.encoded(record)+b'\n')
bound.write_bytes(b''.join(lines));before=bound.read_bytes();assert new.inspect(bound)[1]==1024
try:new.store(bound,{'pending':None,'authority':'none'})
except ValueError:pass
else:raise AssertionError('new capacity unbounded')
assert bound.read_bytes()==before and original.read_bytes()==raw
(out/'REGRESSION.json').write_text(json.dumps({'scope':'local journal construction; no GUI or model success','old_256_refused_without_write':True,'successor_257_accepted':True,'prior_pending_preserved':True,'old_evidence_unchanged':True,'torn_refused':True,'frame_limit_preserved':True,'new_1024_limit_refused_without_write':True,'prior_sha256':hashlib.sha256(raw).hexdigest()},indent=2))
print('PASS bounded journal successor; original pending and hash-chain retained')
