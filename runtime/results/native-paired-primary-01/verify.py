"""Verify retained bytes/outcomes without replaying GUI input or extracting files."""
import hashlib,json,statistics,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'evidence.tar.gz') as t:
 members=t.getmembers()
 assert all(m.isfile() for m in members)
 assert len(members)==len({m.name for m in members})==len(manifest)
 data={m.name:t.extractfile(m).read() for m in members}
assert {k:hashlib.sha256(v).hexdigest() for k,v in data.items()}==manifest
comparison=json.loads((root/'comparison.json').read_text())
assert comparison==json.loads(data['native-paired-comparison-01.json'])
def read(prefix,name):return json.loads(data[prefix+'/'+name])
for arm in ('direct','persistent'):
 prefix='native-paired-'+arm+'-01'
 rows=read(prefix,'tasks.json'); summary=comparison[arm]
 history=[json.loads(l) for l in data[prefix+'/submission-history.jsonl'].splitlines()]
 assert len(history)==len(rows)==6 and all(r['exact'] for r in history)
 assert {r['task_id'] for r in history}=={f'task-{i}' for i in range(1,7)}
 assert read(prefix,'allocation.json')['route']==arm
 assert read(prefix,'goal.json')['seed']==991287
 programs=[]
 for row in rows:
  programs.append(row['navigation']['result']['result'])
  programs.extend([row['direct']['result']] if arm=='direct' else
                  [r for r in (row['entered'],row.get('repaired_enter'),row['saved']) if r and r.get('status')=='completed'])
 for program in programs:
  assert program['status']=='completed'
  releases=program['execution']['releases']
  assert releases and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in releases)
 waits=[json.loads(v) for k,v in data.items() if k.startswith(prefix+'/') and k.endswith('-grounding-timing.json')]
 assert len(waits)==summary['primary_grounding_requests']
 assert len(programs)==summary['released_programs']
 assert sum(w['received_ns']-w['requested_ns'] for w in waits)/1e9==summary['primary_request_response_wait_s']
 assert (read(prefix,'evaluation.json')['known_ns']-read(prefix,'cold-source.json')['capture_ns'])/1e9==summary['cold_capture_to_evaluation_s']
 assert statistics.median(r['through_feedback_ms'] for r in rows)==summary['median_task_execution_through_feedback_ms']
 if arm=='persistent':
  assert rows[3]['entered']['input_dispatched'] is False and rows[3]['refusal_emissions']==0
  assert rows[3]['repaired_enter']['status']=='completed'
failed=read('integrated-six-task-primary-01','evaluation-at-close.json')
assert failed['success'] is False and failed['missing']==['task-4','task-5','task-6']
assert read('integrated-six-task-primary-02','evaluation.json')['success'] is True
print(f'PASS: {len(data)} hashes, both six-task outcomes/releases, refusal, timings and predecessor failure. Not a performance replication.')
