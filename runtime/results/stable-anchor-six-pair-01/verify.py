import hashlib,json,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
with tarfile.open(p/'raw.tar.gz') as t:
    files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
manifest=json.loads((p/'manifest.json').read_text())
assert set(files)==set(manifest)
assert all(hashlib.sha256(files[n]).hexdigest()==h for n,h in manifest.items())
assert hashlib.sha256(files['FREEZE.json']).hexdigest()=='95b1be72a49e6764ef9cd93df36176d14fcbef09ef72c7f6a9a264d442e58b78'
c=json.loads(files['comparison.json'])
assert c==json.loads((p/'comparison.json').read_text())
for arm,ng,nc,np in [('direct',6,25,12),('persistent',2,70,18)]:
    prefix=arm+'/'
    rows=json.loads(files[prefix+'tasks.json'])
    history=[json.loads(v) for v in files[prefix+'submission-history.jsonl'].splitlines()]
    assert len(rows)==len(history)==6
    for i,(r,h,derived) in enumerate(zip(rows,history,c['arms'][arm]['rows']),1):
        assert r['task_id']==h['task_id']==derived['task_id']==f'task-{i}'
        assert h['submitted_values']==[f't991298-{i}']
        review=r['primary_review']
        assert review['status']=='reviewed' and review['decision']['outcome']=='complete'
        assert review['review_received_ns']>=r['feedback_received_ns']
        assert derived['action_to_application_feedback_ms']==r['through_feedback_ms']
        assert derived['action_to_primary_ack_ms']==review['action_to_review_ms']
        assert derived['feedback_to_primary_ack_ms']==review['feedback_to_review_ms']
    gs=[json.loads(v) for n,v in files.items() if n.startswith(prefix) and n.endswith('-grounding-timing.json')]
    assert len(gs)==ng
    assert abs(sum((v['received_ns']-v['requested_ns'])/1e6 for v in gs)-c['arms'][arm]['grounding_wait_ms'])<0.00001
    captures=[json.loads(v) for n,v in files.items() if n.startswith(prefix+'bridge/public-observation-')]
    assert len(captures)==nc
    assert all(v['status']=='returned' and v['input_dispatched'] is False for v in captures)
    reports=[json.loads(v) for n,v in files.items() if n.startswith(prefix) and
             (n.endswith('-navigation-result.json') or n.endswith('-direct-result.json') or '/public-dispatch-' in n)]
    # Direct results are embedded in the task rows rather than separate result files.
    if arm=='direct': reports += [r['direct'] for r in rows]
    assert len(reports)==np
    for r in reports:
        assert r['status']=='returned' and r['result']['status']=='completed'
        releases=r['result']['execution']['releases']
        assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
    evaluation=json.loads(files[prefix+'evaluation-at-close.json'])
    assert evaluation['success'] and evaluation['record_count']==6
    assert not evaluation['missing'] and not evaluation['unexpected'] and not evaluation['duplicates']
    if arm=='persistent':
        assert rows[3]['entered']['status']=='refused' and rows[3]['refusal_emissions']==0
        assert rows[3]['entered']['input_dispatched'] is False
        assert [r['task_id'] for r in rows if 'repaired_enter' in r]==['task-4']
print('PASS scoped retained pair: effects, release, review, repair, capture counts and timings')
