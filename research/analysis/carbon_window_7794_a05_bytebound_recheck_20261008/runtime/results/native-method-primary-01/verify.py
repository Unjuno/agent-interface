"""Verify retained form-method evidence; no extraction, GUI replay or models."""
import hashlib,json,tarfile
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
c='native-method-primary-01/'
source=read('SOURCE.json')
for n,digest in source['files'].items():require(hashlib.sha256(files['candidate/'+n]).hexdigest()==digest,'candidate '+n)
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
require(read('native-method-check-01/result.json')['status']=='PASS','integration tests')
print(f'PASS {len(files)} files; six exact submissions, one zero-emission refusal, explicit repair, verified releases')
