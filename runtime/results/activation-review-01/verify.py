"""Read archived bytes only; verify retained failure, not task success."""
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
def require(value,message):
 if not value:raise ValueError(message)
result=json.loads((root/'result.json').read_text());manifest=json.loads((root/'raw-manifest.json').read_text())
require(hashlib.sha256((root/'raw.tar.gz').read_bytes()).hexdigest()==result['archive_sha256'],'archive')
with tarfile.open(root/'raw.tar.gz','r:gz') as archive:
 members=archive.getmembers();require(len(members)==len(manifest)==result['raw_files'],'inventory')
 data={}
 for member in members:
  require(member.isfile() and member.name in manifest,'member')
  raw=archive.extractfile(member).read();expected=manifest[member.name]
  require(len(raw)==expected['bytes'] and hashlib.sha256(raw).hexdigest()==expected['sha256'],'member bytes')
  data[member.name]=raw
prefix='activation-review-primary-01/'
plan=json.loads(data[prefix+'PLAN.json'])
require(plan['source']==result['source'],'source')
for name,digest in plan['hashes'].items():require(hashlib.sha256(data[prefix+name]).hexdigest()==digest,'frozen '+name)
requests=[json.loads(value) for name,value in data.items() if name.startswith(prefix+'host/request-')]
require(len(requests)==1 and requests[0]['tool']=='interface_guarded_observe','only observation dispatched')
events=[json.loads(line) for line in data[prefix+'host/host-events.jsonl'].splitlines()]
require(events[-1]['kind']=='transport_closed' and events[-1]['code']==0,'transport terminal')
require(not any(e['kind']=='image_reviewed' for e in events),'missing review retained')
effect=json.loads(data[prefix+'session/independent-effect.json'])
require(effect=={'events':[],'A_text':'','B_text':''},'independent no task effects')
terminal=json.loads(data[prefix+'session/primary-terminal.json'])
require(terminal['outcome']=='STOP_CALLER_REVIEW_RECEIPT_ARGUMENT','failure retained')
cleanup=json.loads(data[prefix+'session/cleanup.json'])
require(len(cleanup)==3 and all(type(p['returncode']) is int for p in cleanup),'owned child exits')
require(json.loads(data['activation-review-02/native-exit.json'])['returncode']==0,'native exit')
log=data['activation-review-02/native.stdout'].decode()
require('Ran 345 tests' in log and 'Ran 156 tests' in log and log.count('\nOK')>=2,'native suites')
print('PASS retained bytes/freeze, no-input primary STOP, transport and owned cleanup, final native suites. Primary feature use remains HOLD.')
