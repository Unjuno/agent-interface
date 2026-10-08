"""Issue 3996: finite producer lifecycle experiment; no GUI/model/authority."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

from candidate import classify
from upstream.reader import read_pending
from upstream.delivery_ledger_v2 import DeliveryLedger

ROOT = Path(__file__).resolve().parent
SCENARIOS = ('SEALED_COMPLETE', 'ZERO_EXIT_UNSEALED',
             'NONZERO_EXIT_SEALED', 'SEALED_PARTIAL')
FILES = ('candidate.py', 'run.py', 'audit.py', 'test_candidate.py', 'PLAN.md',
         'ENVIRONMENT.json', 'upstream/reader.py', 'upstream/delivery_ledger_v2.py')
UPSTREAM = {'upstream/reader.py': 'ea72c166c2cea511ea91031dfbb14563fe4e3245',
            'upstream/delivery_ledger_v2.py': 'fb50be9d4d821a7836e6a0158c53a983f0f91df5'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n'


def sources():
    result = {name: sha((ROOT / name).read_bytes()) for name in FILES}
    for name, expected in UPSTREAM.items():
        data = (ROOT / name).read_bytes()
        if hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() != expected:
            raise ValueError('UPSTREAM_CHANGED:' + name)
    return result


def produce(directory, scenario, stream_id):
    frozen = sources()
    ledger = DeliveryLedger()
    records = [ledger.prepare({'event': 'notice', 'payload': {'value': value}})
               for value in ('first', 'late')]
    encoded = [encode(record).encode() for record in records]
    with (directory / 'stream.jsonl').open('xb') as stream:
        stream.write(encoded[0]); stream.flush(); os.fsync(stream.fileno())
        print(encode({'event': 'ready', 'pid': os.getpid(), 'stream_id': stream_id,
                      'scenario': scenario, 'sources': frozen}).rstrip(), flush=True)
        if sys.stdin.buffer.readline() != b'finish\n':
            raise ValueError('MISSING_FINISH_BARRIER')
        stream.write(encoded[1][:-1] if scenario == 'SEALED_PARTIAL' else encoded[1])
        stream.flush(); os.fsync(stream.fileno())
    data = (directory / 'stream.jsonl').read_bytes()
    if scenario != 'ZERO_EXIT_UNSEALED':
        seal = {'schema': 'experimental-final-extent-v1', 'stream_id': stream_id,
                'final_size': len(data), 'last_sequence': 2, 'sha256': sha(data)}
        with (directory / 'seal.json').open('xb') as output:
            output.write(encode(seal).encode()); output.flush(); os.fsync(output.fileno())
    print(encode({'event': 'done', 'pid': os.getpid(), 'stream_id': stream_id,
                  'bytes': len(data), 'sha256': sha(data)}).rstrip(), flush=True)
    return 7 if scenario == 'NONZERO_EXIT_SEALED' else 0


def snapshot(directory):
    path = directory / 'seal.json'
    return {'stream': (directory / 'stream.jsonl').read_text(),
            'seal': path.read_text() if path.exists() else None}


def run_case(directory, scenario, stream_id):
    directory.mkdir()
    command = [sys.executable, '-S', '-B', str(ROOT / 'run.py'), 'producer',
               str(directory), scenario, stream_id]
    trace = {'scenario': scenario, 'stream_id': stream_id, 'command': command,
             'phase_order': [], 'started_ns': time.monotonic_ns()}
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    trace['pid'] = child.pid
    try:
        if not select.select([child.stdout], [], [], 5)[0]:
            raise TimeoutError('PRODUCER_READY_TIMEOUT')
        ready = child.stdout.readline()
        trace['ready_stdout'] = ready.decode()
        event = json.loads(ready)
        if event['event'] != 'ready' or event['pid'] != child.pid or event['sources'] != sources():
            raise ValueError('INVALID_READY')
        trace['phase_order'].append('ready')
        trace['before'] = snapshot(directory)
        first = read_pending(directory / 'stream.jsonl', stream_id=stream_id)
        idle = read_pending(directory / 'stream.jsonl', stream_id=stream_id,
                            cursor=first['next_cursor'])
        trace['first'], trace['idle'] = first, idle
        trace['idle_poll'] = child.poll()
        if trace['idle_poll'] is not None:
            raise ValueError('PRODUCER_NOT_ALIVE_AT_IDLE')
        trace['idle_candidate'] = classify(None, idle, None, stream_id)
        trace['idle_baseline'] = 'COMPLETE' if idle['records'] == [] and idle['tail_state'] == 'end' else 'UNKNOWN'
        trace['phase_order'].append('idle_while_alive')
        trace['stdin'] = 'finish\n'
        trace['phase_order'].append('finish_sent')
        remaining, stderr = child.communicate(b'finish\n', timeout=5)
        trace['stdout'] = ready.decode() + remaining.decode()
        trace['stderr'], trace['exit_code'] = stderr.decode(), child.returncode
        trace['phase_order'].append('joined')
        expected_exit = 7 if scenario == 'NONZERO_EXIT_SEALED' else 0
        if child.returncode != expected_exit or stderr:
            raise ValueError('UNEXPECTED_PRODUCER_EXIT')
        trace['after'] = snapshot(directory)
        late = read_pending(directory / 'stream.jsonl', stream_id=stream_id,
                            cursor=first['next_cursor'])
        final = read_pending(directory / 'stream.jsonl', stream_id=stream_id,
                             cursor=late['next_cursor'])
        trace['late'], trace['final'] = late, final
        seal = json.loads(trace['after']['seal']) if trace['after']['seal'] is not None else None
        trace['final_candidate'] = classify(child.returncode, final, seal, stream_id)
        trace['final_baseline'] = 'COMPLETE' if final['records'] == [] and final['tail_state'] == 'end' else 'UNKNOWN'
        trace['phase_order'].append('final_read')
    except Exception as exc:
        trace['error'] = type(exc).__name__ + ':' + str(exc)
        raise
    finally:
        trace['cleanup_forced'] = child.poll() is None
        if trace['cleanup_forced']:
            child.kill()
            left, err = child.communicate(timeout=5)
            trace['cleanup_stdout'], trace['cleanup_stderr'] = left.decode(), err.decode()
        trace['reaped_exit'] = child.wait(timeout=5)
        trace['ended_ns'] = time.monotonic_ns()
        (directory / 'trace.json').write_text(encode(trace))
    return trace


def run(directory, mode):
    directory.mkdir(parents=True, exist_ok=False)
    identity = sources()
    freeze = json.loads((ROOT / 'FREEZE.json').read_text()) if mode == 'formal' else None
    if freeze is not None and freeze['files'] != identity:
        (directory / 'STOP.json').write_text(encode({'reason': 'SOURCE_FREEZE_MISMATCH'}))
        raise ValueError('SOURCE_FREEZE_MISMATCH')
    result = {'schema': 'issue3996-raw-v1', 'mode': mode, 'sources': identity,
              'freeze_sha256': sha((ROOT / 'FREEZE.json').read_bytes()) if freeze else None,
              'environment': json.loads((ROOT / 'ENVIRONMENT.json').read_text()),
              'rows': [], 'status': 'RUNNING'}
    try:
        for repetition in range(3 if mode == 'formal' else 1):
            for scenario in SCENARIOS:
                case = f'{mode}-{repetition}-{scenario}'
                result['rows'].append(run_case(directory / case, scenario, case))
                (directory / 'raw.json').write_text(encode(result))
        result['status'] = 'EXECUTED_PENDING_AUDIT'
    except Exception as exc:
        result['status'] = 'STOP_EXECUTION'
        result['error'] = type(exc).__name__ + ':' + str(exc)
        raise
    finally:
        (directory / 'raw.json').write_text(encode(result))
    print(encode({'status': result['status'], 'rows': len(result['rows']),
                  'raw_sha256': sha((directory / 'raw.json').read_bytes())}).rstrip())


if __name__ == '__main__':
    if sys.argv[1] == 'producer':
        raise SystemExit(produce(Path(sys.argv[2]), sys.argv[3], sys.argv[4]))
    if sys.argv[1] not in ('construction', 'formal'):
        raise SystemExit('usage: run.py construction|formal NEW_DIRECTORY')
    run(Path(sys.argv[2]), sys.argv[1])
