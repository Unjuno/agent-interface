import hashlib,json,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
with tarfile.open(p/'raw.tar.gz') as t:
    files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
manifest=json.loads((p/'manifest.json').read_text())
assert set(files)==set(manifest)
assert all(hashlib.sha256(files[n]).hexdigest()==h for n,h in manifest.items())
result=json.loads(files['RESULT.json'])
assert result==json.loads((p/'RESULT.json').read_text())
assert len(result['rows'])==12 and not result['comparison_valid']
direct=json.loads(files['direct-startup.json'])
assert direct['exit_code']==1 and direct['out_created'] is False
evaluation=json.loads(files['persistent/evaluation-at-close.json'])
assert evaluation['success'] is False
assert list(evaluation['exact_counts'].values())==[1,1,1,0,0,0]
assert not evaluation['unexpected'] and not evaluation['duplicates']
rows=json.loads(files['persistent/tasks.json'])
assert [r['task_id'] for r in rows]==['task-1','task-2','task-3','task-4']
for i in (0,3):
    assert rows[i]['entered']['status']=='refused'
    assert rows[i]['entered']['input_dispatched'] is False
    assert rows[i]['refusal_emissions']==0
assert 'unplanned partial or repeated refusal' in files['persistent/error.txt'].decode()
assert json.loads(files['persistent/task-1-review-correction.json'])['original_review_preserved']
history=[json.loads(line) for line in files['persistent/submission-history.jsonl'].splitlines()]
assert len(history)==3
for i,row in enumerate(history,1):
    assert row['task_id']==f'task-{i}'
    assert row['submitted_values']==[f't991297-{i}']
print('PASS retention only: complete failed-pair accounting, refusals and review correction')
