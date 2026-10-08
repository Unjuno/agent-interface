"""Read-only checks of retained bytes and scoped outcomes; no extraction/input."""
import ast
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

BASE = Path(__file__).resolve().parent

def require(value, message):
    if not value:
        raise ValueError(message)

def main():
    manifest = json.loads((BASE / 'manifest.json').read_text())
    archive = (BASE / 'raw.tar.gz').read_bytes()
    require(hashlib.sha256(archive).hexdigest() == manifest['archive_sha256'], 'archive digest')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tf:
        for m in tf.getmembers():
            p = PurePosixPath(m.name)
            require(m.isfile() and not p.is_absolute() and '..' not in p.parts, 'unsafe archive member')
            require(m.name not in files, 'duplicate member')
            files[m.name] = tf.extractfile(m).read()
    require(set(files) == set(manifest['files']), 'member inventory')
    for n, b in files.items():
        expected = manifest['files'][n]
        require(len(b) == expected['bytes'] and hashlib.sha256(b).hexdigest() == expected['sha256'], 'member digest: '+n)
    def read(name):
        return json.loads(files['allocation/'+name])
    def releases(value):
        found = 0
        if isinstance(value, dict):
            if 'execution' in value and isinstance(value['execution'], dict):
                ex = value['execution']
                if ex.get('program_emissions', ex.get('emissions', 0)) > 0:
                    rs = ex.get('releases', [])
                    require(bool(rs) and all(r.get('verified') is True and r.get('keys_down') == [] and r.get('buttons_down') == [] for r in rs), 'input release')
                    found += 1
            for item in value.values():
                found += releases(item)
        elif isinstance(value, list):
            for item in value:
                found += releases(item)
        return found
    plan = read('PLAN.json')
    require(plan['source_revision'].startswith('3b955b970') and plan['seed'] == 991701, 'frozen source/seed')
    require(hashlib.sha256(files['allocation/runner-source.py']).hexdigest() == plan['runner_sha256'], 'runner source')
    summary = {}
    task_schedules = []
    for route in ['persistent']:
        goals = read(route+'/goal.json')['tasks']
        task_schedules.append([{k:t[k] for k in ['task_id','token','layout','phase']} for t in goals])
        records = [json.loads(line) for line in files['allocation/'+route+'/submission-history.jsonl'].decode().splitlines()]
        require(len(records) == 6, 'six independent submissions')
        counts = {}
        for task in goals:
            rs = [r for r in records if r['task_id'] == task['task_id']]
            counts[task['task_id']] = len(rs)
            require(len(rs) == 1 and rs[0]['submitted_values'] == [task['token']] and rs[0]['expected_token'] == task['token'] and rs[0]['layout'] == task['layout'], 'exact payload/layout/no duplicate')
        require(len(counts) == 6 and all(r['task_id'] in counts for r in records), 'task inventory')
        rows = read(route+'/tasks.json')
        require(len(rows) == 6 and [r['task_id'] for r in rows] == [t['task_id'] for t in goals], 'receipt schedule')
        release_checks = releases(rows)
        require(release_checks == (12 if route == 'direct' else 18), 'input release count')
        for i in range(1,7):
            req = read(f'{route}/task-{i}-primary-review-request.json')
            decision = read(f'{route}/task-{i}-primary-review.json')
            outcome = read(f'{route}/task-{i}-primary-review-result.json')
            artifact = req['source']['native']['artifact']
            image = files['allocation/'+route+'/bridge/images/'+Path(artifact['path']).name]
            require(hashlib.sha256(image).hexdigest() == artifact['sha256'] and len(image) == artifact['bytes'], 'review PNG')
            require(decision['source_sequence'] == req['source_sequence'] and decision['task_id'] == req['task_id'] and decision['outcome'] == 'complete', 'explicit source decision')
            require(outcome['status'] == 'reviewed' and outcome['decision'] == decision, 'accepted review')
        groundings = ['cold'] + ([f'task-{i}' for i in range(2,7)] if route == 'direct' else ['repair'])
        for name in groundings:
            source = read(route+'/'+name+'-source.json')
            grounding = read(route+'/'+name+'-grounding.json')
            require(grounding['source_sequence'] == source['sequence'], 'grounding source')
            artifact = source['native']['artifact']
            image = files['allocation/'+route+'/bridge/images/'+Path(artifact['path']).name]
            require(hashlib.sha256(image).hexdigest() == artifact['sha256'], 'grounding image')
        origin=read(route+'/runtime-origin.json')
        require(all('/runtime.pyz/runtime/' in origin[k] for k in ['bridge','api']), 'portable runtime origin')
        require(read('outer-exits.json')[route]['exit_code'] == 0, 'outer terminal success')
        summary[route] = {'exact_counts':counts,'accepted_primary_reviews':6,'primary_groundings':len(groundings),'primary_images_delivered':6+len(groundings),'retained_backend_observations':sum(n.startswith('allocation/'+route+'/bridge/observation-') for n in files),'release_records_checked':release_checks,'through_feedback_ms':[r['through_feedback_ms'] for r in rows],'action_to_primary_review_ms':[read(f'{route}/task-{i}-primary-review-result.json')['action_to_review_ms'] for i in range(1,7)],'cleanup':read(route+'/cleanup.json')}
    stale = read('persistent/tasks.json')[3]
    require(stale['entered']['status'] == 'refused' and stale['entered']['input_dispatched'] is False and stale['refusal_emissions'] == 0, 'stale refusal')
    require(stale['repaired_enter']['status'] == 'completed' and stale['saved']['status'] == 'completed', 'explicit recovery')
    observations = [json.loads(b) for n,b in files.items() if n.startswith('allocation/persistent/bridge/observation-')]
    require(len(observations) == 70 and all(o['image_source'] == 'exact_capture_rgb_handoff' for o in observations), 'current RGB handoff accounting')
    for o in observations:
        a = o['native']['artifact']
        png = files['allocation/persistent/bridge/images/'+Path(a['path']).name]
        require(hashlib.sha256(png).hexdigest() == a['sha256'] and a['source_raw_sha256'] == o['native']['sha256'], 'every capture PNG/raw link')
    native = json.loads(files['native/result.json'])
    require(native['status'] == 'PASS' and all(s['returncode'] == 0 for s in native['suites']), 'native suites')
    require(b'Ran 10 tests' in files['checks/capture-rgb-handoff-tests.txt'] and files['checks/capture-rgb-handoff-tests.txt'].rstrip().endswith(b'OK'), 'handoff/corruption tests')
    with zipfile.ZipFile(io.BytesIO(files['allocation/runtime.pyz'])) as z:
        for name in ['runtime/backends/x11_v1/capture_artifacts.py','runtime/backends/x11_v1/backend.py','runtime/guarded_x11_v1/bridge.py']:
            require(z.read(name) == files['source/'+name], 'candidate package source')
    summary['persistent']['rgb_handoff_interval_sum_ms']=sum((o['timing_ns']['decoded']-o['timing_ns']['artifact_verified'])/1e6 for o in observations)
    summary['scope']='scoped current-capture handoff and primary fixed-fixture completion; HOLD_INTEGRATION_INCOMPLETE; no causal latency/token claim'
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
