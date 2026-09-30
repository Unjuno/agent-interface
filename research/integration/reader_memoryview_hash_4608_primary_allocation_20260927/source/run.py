import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from common import corpus_bytes, sha256_bytes, sha256_path


def durable_json(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    with open(path, 'xb', buffering=0) as f:
        f.write(raw); os.fsync(f.fileno())


def durable_append(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    with open(path, 'ab', buffering=0) as f:
        f.write(raw); os.fsync(f.fileno())


def invoke(argv, timeout, root, out, journal, worker_id, meta):
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', PYTHONUNBUFFERED='1')
    start = time.time_ns()
    proc = subprocess.Popen(argv, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    started = {'event': 'worker_started', 'worker_id': worker_id, **meta, 'pid': proc.pid,
               'started_ns': start, 'argv': argv, 'argv_sha256': hashlib.sha256(
                   json.dumps(argv, separators=(',', ':')).encode()).hexdigest()}
    durable_append(journal, started)
    category = 'EXITED'
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        category = 'TIMEOUT'
        proc.kill()
        stdout, stderr = proc.communicate()
        code = 124
    ended = time.time_ns()
    rec = {'kind': meta['kind'], **meta, 'worker_id': worker_id, 'pid': proc.pid,
           'argv': argv, 'exit': code, 'stdout': stdout, 'stderr': stderr,
           'started_ns': start, 'ended_ns': ended, 'category': category}
    durable_append(journal, {'event': 'worker_completed', 'worker_id': worker_id,
                             'pid': proc.pid, 'ended_ns': ended, 'exit': code,
                             'category': category, 'stdout_sha256': hashlib.sha256(stdout.encode()).hexdigest(),
                             'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest()})
    durable_append(out / 'RAW.jsonl', rec)
    return rec


p = argparse.ArgumentParser()
p.add_argument('--phase', choices=['construction', 'formal'], required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
root = Path(__file__).resolve().parent
bundle = root.parent
freeze_bytes = (bundle / 'FREEZE.json').read_bytes()
freeze_digest = hashlib.sha256(freeze_bytes).hexdigest()
freeze_sidecar = (bundle / 'FREEZE.sha256').read_text().split()[0]
if freeze_digest != freeze_sidecar:
    raise SystemExit('FREEZE_HASH_MISMATCH')
freeze = json.loads(freeze_bytes)
for name, expected in freeze['metadata_sha256'].items():
    if sha256_path(bundle / name) != expected:
        raise SystemExit('FROZEN_METADATA_MISMATCH:' + name)
for name, expected in freeze['source_sha256'].items():
    if sha256_path(root / name) != expected:
        raise SystemExit('FROZEN_SOURCE_MISMATCH:' + name)
out = Path(a.out)
out.mkdir(parents=True, exist_ok=False)
(out / 'journal.jsonl').touch(exist_ok=False)
(out / 'RAW.jsonl').touch(exist_ok=False)
started = time.time_ns()
records = 64 if a.phase == 'construction' else 4096
cursors = [0, 32, 64] if a.phase == 'construction' else [0, 2048, 4064, 4096]
reps = 1 if a.phase == 'construction' else 3
data = corpus_bytes(records)
corpus = out / 'corpus.jsonl'
with corpus.open('xb', buffering=0) as f:
    f.write(data); os.fsync(f.fileno())
sources = ['baseline_reader.py', 'candidate_reader.py', 'common.py', 'worker.py',
           'contract_worker.py', 'run.py', 'audit.py', 'controls.py', 'durability_test.py']
source_sha = {name: sha256_path(root / name) for name in sources}
durable_json(out / 'INVOCATION.json', {'schema': 'reader-memoryview-invocation-v2',
    'phase': a.phase, 'records': records, 'cursor_records': cursors, 'repetitions': reps,
    'max_records': 32, 'corpus_bytes': len(data), 'corpus_sha256': sha256_bytes(data),
    'source_sha256': source_sha, 'started_ns': started, 'runner_pid': os.getpid()})
durable_append(out / 'journal.jsonl', {'event': 'runner_started', 'phase': a.phase,
    'pid': os.getpid(), 'started_ns': started, 'corpus_sha256': sha256_bytes(data),
    'source_sha256': source_sha})
resource = []
stop = None
for cur in cursors:
    for rep in range(reps):
        order = ['BASELINE', 'MEMORYVIEW'] if rep % 2 == 0 else ['MEMORYVIEW', 'BASELINE']
        for arm in order:
            wid = f'resource:{cur}:{rep}:{arm}'
            cmd = [sys.executable, '-B', str(root / 'worker.py'), '--arm', arm,
                   '--corpus', str(corpus), '--cursor-records', str(cur), '--max-records', '32']
            meta = {'kind': 'resource', 'cursor_records': cur, 'rep': rep, 'arm': arm}
            rec = invoke(cmd, 8, root, out, out / 'journal.jsonl', wid, meta)
            resource.append(rec)
            if rec['exit'] != 0:
                stop = {'classification': 'STOP_WORKER_' + rec['category'], 'worker_id': wid,
                        'exit': rec['exit'], 'completed_ns': rec['ended_ns']}
                break
        if stop: break
    if stop: break
contracts = []
if stop is None and len(resource) == len(cursors) * reps * 2:
    for arm in ['BASELINE', 'MEMORYVIEW']:
        wid = f'contract:{arm}'
        cmd = [sys.executable, '-B', str(root / 'contract_worker.py'), '--arm', arm]
        rec = invoke(cmd, 8, root, out, out / 'journal.jsonl', wid, {'kind': 'contract', 'arm': arm})
        contracts.append(rec)
        if rec['exit'] != 0:
            stop = {'classification': 'STOP_CONTRACT_' + rec['category'], 'worker_id': wid,
                    'exit': rec['exit'], 'completed_ns': rec['ended_ns']}
            break
summary = {'schema': 'reader-memoryview-run-v2', 'phase': a.phase, 'records': records,
    'corpus_bytes': len(data), 'corpus_sha256': sha256_bytes(data), 'resource': resource,
    'contracts': contracts, 'started_ns': started, 'ended_ns': time.time_ns(),
    'runner_pid': os.getpid(), 'source_sha256': source_sha}
durable_json(out / 'RAW.json', summary)
if stop:
    durable_json(out / 'STOP.json', stop)
durable_append(out / 'journal.jsonl', {'event': 'runner_completed', 'phase': a.phase,
    'pid': os.getpid(), 'ended_ns': summary['ended_ns'], 'classification': stop or 'COMPLETED'})
print(json.dumps({'phase': a.phase, 'resource_rows': len(resource), 'contracts': len(contracts),
    'all_exit_zero': stop is None and all(x['exit'] == 0 for x in resource + contracts),
    'raw_sha256': sha256_path(out / 'RAW.json')}, sort_keys=True))
raise SystemExit(1 if stop else 0)
