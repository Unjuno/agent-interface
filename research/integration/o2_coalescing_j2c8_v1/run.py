"""One consumed batch; exact actor bytes and actual waits are retained."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from fixtures import CONDITIONS, MODES, make

ROOT = Path(__file__).resolve().parent


def call(role, data):
    stdin = json.dumps(data, sort_keys=True, separators=(',', ':')) + '\n'
    argv = [sys.executable, '-B', str(ROOT / 'actor.py'), role]
    env = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'OPENBLAS_NUM_THREADS': '1',
           'OMP_NUM_THREADS': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
    start = time.monotonic_ns()
    p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=env)
    timed_out = False
    try:
        out, err = p.communicate(stdin.encode(), timeout=5)
    except subprocess.TimeoutExpired:
        timed_out = True
        p.kill()
        out, err = p.communicate()
    receipt = {'argv': argv, 'pid': p.pid, 'stdin': stdin,
               'stdout': out.decode(), 'stderr': err.decode(),
               'returncode': p.returncode, 'timed_out': timed_out,
               'start_ns': start, 'end_ns': time.monotonic_ns()}
    return receipt


def run(out, batch, construction):
    if not construction:
        frozen = json.loads((ROOT / 'FREEZE.json').read_text())
        for name, digest in frozen['files'].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError('source changed: ' + name)
    schedule = [('SINGLE', 0), ('CHANGE_BURST', 0), ('CRITICAL_BURST', 0)] if construction else [(CONDITIONS[batch], r) for r in range(2)]
    count = 0
    with (out / 'records.jsonl').open('x') as log:
        for condition, rep in schedule:
            for mode in MODES:
                identity = ('construction' if construction else 'formal') + ':' + condition + ':' + str(rep) + ':' + mode
                source_identity = identity.rsplit(':', 1)[0]
                request = make(condition, source_identity, mode, small=construction)
                producer = call('produce', request)
                row = {'id': identity, 'condition': condition, 'rep': rep,
                       'mode': mode, 'producer': producer}
                if producer['returncode'] == 0 and not producer['timed_out']:
                    value = json.loads(producer['stdout'])
                    row['consumer'] = call('consume', {'messages': value['messages']})
                log.write(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')
                log.flush()
                os.fsync(log.fileno())
                count += 1
                if 'consumer' not in row or any(row[x]['returncode'] != 0 or row[x]['timed_out'] or row[x]['stderr'] for x in ('producer', 'consumer')):
                    raise RuntimeError('actor STOP; see retained row')
    (out / 'END.json').write_text(json.dumps({'rows': count, 'batch': batch, 'construction': construction}, sort_keys=True) + '\n')


if __name__ == '__main__':
    run(Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3].startswith('construction'))
