"""Verify retained form-method evidence; no extraction, GUI replay or models."""
import hashlib,json,tarfile,io,zipfile
from pathlib import Path
root=Path(__file__).parent
def require(ok,why):
    if not ok:raise ValueError(why)
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(all(m.isfile() for m in members),'regular files')
    require(len(members)==len({m.name for m in members}),'unique paths')
    files={m.name:archive.extractfile(m).read() for m in members}
manifest=json.loads((root/'manifest.json').read_text())
require(set(files)==set(manifest),'inventory')
for n,digest in manifest.items():require(hashlib.sha256(files[n]).hexdigest()==digest,n)
def read(n):return json.loads(files[n])
c='shared-x11-runtime-primary-01/'
build=read('shared-x11-runtime-build-01/manifest.json')
raw=files['shared-x11-runtime-build-01/runtime.pyz']
require(hashlib.sha256(raw).hexdigest()==build['sha256'], 'built archive hash')
require(build['source_revision']==read(c+'SUMMARY.json')['source_revision'], 'committed build identity')
origin=read(c+'runtime-origin.json')
require(origin['bridge']==origin['archive']+'/runtime/guarded_x11_v1/bridge.py', 'bridge from archive')
require(origin['api']==origin['archive']+'/runtime/cli_v1/api.py', 'dispatch from archive')
with zipfile.ZipFile(io.BytesIO(raw)) as portable:
    require(not any(n.startswith('research/') for n in portable.namelist()), 'no research tree')
    require('runtime/guarded_x11_v1/bridge.py' in portable.namelist(), 'shared implementation packaged')
    require(json.loads(portable.read('BUILD.json'))['source_revision']==build['source_revision'], 'internal build identity')
goals=read(c+'goal.json')['tasks'];rows=read(c+'tasks.json')
history=[json.loads(x) for x in files[c+'submission-history.jsonl'].decode().splitlines()]
require(len(goals)==len(rows)==len(history)==6,'six tasks')
require(len({r['task_id'] for r in history})==6,'exactly once')
evaluation=read(c+'evaluation.json');require(evaluation['success'] is True,'independent evaluation')
for task,row,record in zip(goals,rows,history):
    name=task['task_id']; require(row['task_id']==record['task_id']==name,'task identity')
    require(record['submitted_values']==[task['token']] and record['exact'] is True,'exact effect')
    review=read(c+name+'-primary-review-result.json')
    require(review['status']=='reviewed' and review['decision']['outcome']=='complete','primary review')
    require(review['review_received_ns']<evaluation['known_ns'],'review before final oracle')
    method=row.get('repaired_method',row['method'])
    require(method['status']=='completed' and method['completed_actions']==2,'two guarded steps')
    require(method['task_success'] is None and method['replay_allowed'] is False,'no semantic inference/replay')
    for key in ('repaired_enter' if 'repaired_enter' in row else 'entered','saved'):
        result=row[key];require(result['status']=='completed' and result['recovery_required'] is False,'input completion')
        require(all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in result['execution']['releases']),'released')
        require(result['guard_checks'] and all(g['status']=='VALID' for g in result['guard_checks']),'target guards')
refused=rows[3]
require(refused['entered']['status']=='refused' and refused['entered']['input_dispatched'] is False,'old reference refused')
require(refused['refusal_emissions']==0 and refused['method']['stopped_at']=='entered','zero input before repair')
require(refused['method']['completed_actions']==0 and refused['repaired_method']['completed_actions']==2,'retained repair boundary')
for n,data in files.items():
    if n.startswith(c+'bridge/observation-') and n.endswith('.json'):
        observation=json.loads(data);artifact=observation['native']['artifact']
        image=c+'bridge/images/'+Path(artifact['path']).name
        require(hashlib.sha256(files[image]).hexdigest()==artifact['sha256'],'observation pixels')
require(all(p['returncode'] is not None for p in read(c+'cleanup.json')),'tracked processes terminal')
require(read(c+'EXIT.json')['exit_code']==0,'harness exit')
require(read('shared-x11-runtime-check-02/result.json')['status']=='PASS','integration tests')
print(f'PASS {len(files)} files; six exact submissions, one zero-emission refusal, explicit repair, verified releases')

with tarfile.open(root/'ci-repair.tar.gz') as archive:
    members=archive.getmembers()
    require(all(m.isfile() for m in members), 'repair regular files')
    require(len(members)==len({m.name for m in members}), 'repair unique paths')
    repair={m.name:archive.extractfile(m).read() for m in members}
repair_manifest=json.loads((root/'ci-repair-manifest.json').read_text())
require(set(repair)==set(repair_manifest), 'repair inventory')
for name,digest in repair_manifest.items():
    require(hashlib.sha256(repair[name]).hexdigest()==digest, name)
check=json.loads(repair['shared-x11-runtime-check-03/result.json'])
require(check['status']=='PASS' and all(s['returncode']==0 for s in check['suites']), 'repaired local checks')
for name in ('no-site-distribution.log', 'cli-local.log', 'x11-extra.log'):
    require(repair['shared-x11-ci-repair-01/'+name].rstrip().endswith(b'OK'), name)
print(f'PASS {len(repair)} supplementary files; initial CI failures and corrected local checks retained')
