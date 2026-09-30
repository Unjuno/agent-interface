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
    summary = {}
    for route, wanted in [('persistent', 6), ('direct', 1)]:
        goals = read(route+'/goal.json')['tasks']
        records = [json.loads(line) for line in files['allocation/'+route+'/submission-history.jsonl'].decode().splitlines()]
        require(len(records) == wanted, 'retained submission count')
        counts = {}
        for task in goals:
            rs = [r for r in records if r['task_id'] == task['task_id']]
            counts[task['task_id']] = len(rs)
            require(all(r['submitted_values'] == [task['token']] and r['expected_token'] == task['token'] and r['layout'] == task['layout'] for r in rs), 'independent exact payload/layout')
        require(list(counts.values()) == ([1]*6 if route == 'persistent' else [1,0,0,0,0,0]), 'task accounting')
        require(all(r['task_id'] in counts for r in records), 'unexpected task')
        rows = read(route+'/tasks.json')
        require(len(rows) == wanted, 'completed receipt count')
        release_checks = releases(rows)
        reviews = []
        for i in range(1, wanted+1):
            req = read(f'{route}/task-{i}-primary-review-request.json')
            decision = read(f'{route}/task-{i}-primary-review.json')
            outcome = read(f'{route}/task-{i}-primary-review-result.json')
            artifact = req['source']['native']['artifact']
            image = files['allocation/'+route+'/bridge/images/'+Path(artifact['path']).name]
            require(hashlib.sha256(image).hexdigest() == artifact['sha256'] and len(image) == artifact['bytes'], 'review image bytes')
            require(decision['source_sequence'] == req['source_sequence'] and decision['task_id'] == req['task_id'], 'decision source binding')
            if route == 'persistent':
                require(outcome['status'] == 'reviewed' and outcome['decision'] == decision and decision['outcome'] == 'complete', 'accepted primary review')
            else:
                require(outcome['status'] == 'unavailable' and 'Expecting value' in outcome['error'], 'original review STOP preserved')
            reviews.append(outcome['status'])
        summary[route] = {'exact_counts':counts, 'release_records_checked':release_checks, 'primary_reviews':reviews, 'cleanup':read(route+'/cleanup.json'), 'through_feedback_ms':[r['through_feedback_ms'] for r in rows]}
    stale = read('persistent/tasks.json')[3]
    require(stale['entered']['status'] == 'refused' and stale['entered']['input_dispatched'] is False and stale['refusal_emissions'] == 0, 'stale zero-input refusal')
    require(stale['repaired_enter']['status'] == 'completed' and stale['saved']['status'] == 'completed', 'explicit recovery')
    require(read('outer-exits.json')['direct']['exit_code'] == 1 and read('outer-exits.json')['persistent']['exit_code'] == 0, 'outer outcomes')
    probe = read('publication-probe/probe.json')
    require(probe['first_exit'] == 0 and probe['duplicate_exit'] == 2 and probe['partial_stdin_final_slot_absent'] is True and probe['receiver_parsed_complete_value'] is True and probe['input_dispatched'] is False, 'publication probe')
    require(read('publication-probe/atomic-review.json') == read('direct/task-1-primary-review.json'), 'exact published value')
    require(read('publication-probe/duplicate.stdout.json')['replay_allowed'] is False, 'duplicate no replay')
    old = files['source/research/live_control/native_exchange_v1.py'].decode()
    new = files['source/runtime/host_v1/file_publication.py'].decode()
    def functions(source):
        return {n.name:ast.get_source_segment(source,n) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    require(all(functions(old)[n] == functions(new)[n] for n in ['encoded','publish']), 'unchanged promotion')
    with zipfile.ZipFile(io.BytesIO(files['allocation/publication-runtime.pyz'])) as z:
        require(z.read('runtime/host_v1/file_publication.py') == new.encode(), 'candidate archive publisher')
    native = json.loads(files['native/result.json'])
    require(native['status'] == 'PASS' and all(s['returncode'] == 0 for s in native['suites']), 'native suites')
    summary['scope'] = 'retained mechanical evidence; HOLD_INTEGRATION_INCOMPLETE; not human tempo/token/model-visibility evidence'
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
