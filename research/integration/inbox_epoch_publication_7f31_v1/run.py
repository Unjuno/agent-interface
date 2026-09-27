"""Issue 3938: isolated publication interleavings, not a production host."""
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import platform
import select
import shutil
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
POLICIES = ('CALLER_ID_ONLY', 'SIDECAR_PRECHECK', 'PIN_ONCE')
SCHEDULES = ('STABLE_A', 'SWITCH_BEFORE_PREPARE', 'SWITCH_BETWEEN_CHECK_AND_READ',
             'SWITCH_AFTER_READ_BEFORE_RETURN', 'FRESH_B_CURSOR')
UPSTREAM = {
    'research/integration/event_inbox_reader_v1/reader.py': 'ea72c166c2cea511ea91031dfbb14563fe4e3245',
    'research/live_control/delivery_ledger_v2.py': 'fb50be9d4d821a7836e6a0158c53a983f0f91df5',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_ids():
    result = {}
    for name, expected in UPSTREAM.items():
        data = (REPO / name).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != expected:
            raise RuntimeError('STOP_UPSTREAM_BLOB_MISMATCH:' + name)
        result[name] = {'git_blob': blob, 'sha256': sha(data)}
    return result


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def emit(value):
    print(json.dumps(value, sort_keys=True, separators=(',', ':')), flush=True)


def worker(role, root):
    sources = source_ids()
    reader = load('frozen_reader', REPO / list(UPSTREAM)[0])
    spec = json.loads((root / 'request.json').read_text())
    chosen, problem, receipt = None, None, None
    emit({'ready': role, 'pid': os.getpid(), 'sources': sources})
    for line in sys.stdin:
        command = json.loads(line)['command']
        if command == 'quit':
            emit({'done': 'quit'})
            return
        if role == 'publisher':
            if command != 'publish':
                raise ValueError('invalid publisher command')
            old = os.readlink(root / 'CURRENT')
            os.symlink('epochs/B', root / 'NEXT')
            os.replace(root / 'NEXT', root / 'CURRENT')
            emit({'done': 'publish', 'before': old, 'after': os.readlink(root / 'CURRENT')})
        elif command == 'prepare':
            chosen = root / 'CURRENT'
            if spec['policy'] == 'PIN_ONCE':
                chosen = chosen.resolve(strict=True)
            observed_epoch = None
            if spec['policy'] != 'CALLER_ID_ONLY':
                observed_epoch = json.loads((chosen / 'epoch.json').read_text())['epoch']
                if observed_epoch != spec['stream_id']:
                    problem = 'EPOCH_MISMATCH'
            emit({'done': 'prepare', 'selected': str(chosen.relative_to(root)),
                  'observed_epoch': observed_epoch, 'problem': problem})
        elif command == 'read':
            if chosen is None:
                raise RuntimeError('read before prepare')
            if problem is None:
                receipt = reader.read_pending(chosen / 'delivered.jsonl',
                    stream_id=spec['stream_id'], cursor=spec['cursor'])
            emit({'done': 'read', 'problem': problem})
        elif command == 'return':
            emit({'done': 'return', 'problem': problem, 'receipt': receipt})
        else:
            raise ValueError('invalid reader command')


def snapshot(root):
    result = {}
    for gen in ('A', 'B'):
        for name in ('epoch.json', 'delivered.jsonl'):
            p = root / 'epochs' / gen / name
            data = p.read_bytes()
            st = p.stat()
            result[f'{gen}/{name}'] = {'text': data.decode(), 'sha256': sha(data),
                'size': st.st_size, 'inode': st.st_ino, 'device': st.st_dev}
    return result


def one_case(root, policy, schedule, repetition):
    root.mkdir()
    ledger_type = load('frozen_ledger', REPO / list(UPSTREAM)[1]).DeliveryLedger
    reader = load('setup_reader', REPO / list(UPSTREAM)[0])
    for gen in ('A', 'B'):
        target = root / 'epochs' / gen
        target.mkdir(parents=True)
        ledger = ledger_type()
        items = [ledger.prepare({'event': 'notification', 'payload': {'value': value}})
                 for value in ('common-1', 'common-2', gen + '-tail')]
        (target / 'delivered.jsonl').write_text(''.join(
            json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n' for x in items))
        (target / 'epoch.json').write_text(json.dumps({'epoch': gen}, sort_keys=True) + '\n')
    os.symlink('epochs/A', root / 'CURRENT')
    initial = reader.read_pending(root / 'epochs/A/delivered.jsonl', stream_id='A', max_records=1)
    spec = {'policy': policy, 'stream_id': 'B' if schedule == 'FRESH_B_CURSOR' else 'A',
            'cursor': None if schedule == 'FRESH_B_CURSOR' else initial['next_cursor']}
    (root / 'request.json').write_text(json.dumps(spec, sort_keys=True))
    row = {'id': root.name, 'policy': policy, 'schedule': schedule, 'repetition': repetition,
           'request': spec, 'initial': initial, 'before': snapshot(root),
           'events': [], 'processes': {}, 'exits': {}}
    children = {}

    def receive(role, command):
        child = children[role]
        if not select.select([child.stdout], [], [], 8)[0]:
            raise TimeoutError(role + ':' + command)
        raw = child.stdout.readline()
        if not raw or len(raw) > 100000:
            raise RuntimeError('invalid worker response')
        value = json.loads(raw)
        row['events'].append({'actor': role, 'command': command, 'stdout': raw.decode(),
            'current': os.readlink(root / 'CURRENT'), 'observed_ns': time.perf_counter_ns()})
        (root / 'partial.json').write_text(json.dumps(row, sort_keys=True))
        return value

    def request(role, command):
        child = children[role]
        child.stdin.write((json.dumps({'command': command}) + '\n').encode())
        child.stdin.flush()
        return receive(role, command)

    try:
        for role in ('reader', 'publisher'):
            command = [sys.executable, '-S', '-B', str(Path(__file__).resolve()), 'worker', role, str(root)]
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, bufsize=0)
            children[role] = child
            row['processes'][role] = {'pid': child.pid, 'command': command}
            receive(role, 'ready')
        if schedule in ('SWITCH_BEFORE_PREPARE', 'FRESH_B_CURSOR'):
            request('publisher', 'publish')
        request('reader', 'prepare')
        if schedule == 'SWITCH_BETWEEN_CHECK_AND_READ':
            request('publisher', 'publish')
        request('reader', 'read')
        if schedule == 'SWITCH_AFTER_READ_BEFORE_RETURN':
            request('publisher', 'publish')
        request('reader', 'return')
        for role, child in children.items():
            request(role, 'quit')
            child.stdin.close()
            code = child.wait(timeout=8)
            stderr = child.stderr.read().decode()
            trailing = child.stdout.read().decode()
            row['exits'][role] = {'code': code, 'stderr': stderr, 'trailing_stdout': trailing}
            if code != 0 or stderr or trailing:
                raise RuntimeError('STOP_WORKER_EXIT:' + role)
    except BaseException:
        row['error'] = traceback.format_exc()
        raise
    finally:
        for role, child in children.items():
            if child.poll() is None:
                child.kill()
                child.wait(timeout=8)
            if role not in row['exits']:
                row['exits'][role] = {'code': child.returncode, 'stderr': child.stderr.read().decode(),
                                      'trailing_stdout': child.stdout.read().decode()}
            for pipe in (child.stdin, child.stdout, child.stderr):
                if not pipe.closed:
                    pipe.close()
        row['after'] = snapshot(root)
        row['final_current'] = os.readlink(root / 'CURRENT')
        (root / 'case.json').write_text(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')
    return row


def run(root, construction):
    root.mkdir(parents=True, exist_ok=False)
    frozen = json.loads((HERE / 'FREEZE.json').read_text()) if not construction else None
    if frozen:
        for name, digest in frozen['sha256'].items():
            if sha((REPO / name).read_bytes()) != digest:
                raise RuntimeError('STOP_FREEZE_MISMATCH:' + name)
    raw = {'schema': 'issue3938-raw-v1', 'allocation': root.name, 'construction': construction,
           'sources': source_ids(), 'freeze': frozen, 'environment': {
               'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(),
               'docker_cli': shutil.which('docker'), 'pid': os.getpid()}, 'cases': []}
    try:
        for policy, schedule, repetition in itertools.product(POLICIES, SCHEDULES,
                                                             range(1, 2 if construction else 4)):
            name = f'{policy}-{schedule}-{repetition}'
            raw['cases'].append(one_case(root / name, policy, schedule, repetition))
    except BaseException:
        raw['stop'] = traceback.format_exc()
        raise
    finally:
        with (root / 'raw.json').open('x') as output:
            json.dump(raw, output, sort_keys=True, separators=(',', ':'))
            output.write('\n')
    emit({'raw': str(root / 'raw.json'), 'cases': len(raw['cases']), 'scientific_verdict': 'NOT_COMPUTED_BY_RUNNER'})


if __name__ == '__main__':
    if sys.argv[1] == 'worker':
        worker(sys.argv[2], Path(sys.argv[3]).resolve())
    elif sys.argv[1] in ('construction', 'formal'):
        run(Path(sys.argv[2]).resolve(), sys.argv[1] == 'construction')
    else:
        raise SystemExit('Usage: run.py construction|formal NEW_OUTPUT_DIRECTORY')
