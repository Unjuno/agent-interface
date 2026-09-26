"""Issue 3947: local file-kind admission experiment, never a production reader."""
import base64
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import tempfile
import time
from upstream.reader import read_pending

ROOT = Path(__file__).resolve().parent
POLICIES = ('EXACT_READER', 'REGULAR_SNAPSHOT_ADAPTER')
CASES = ('COMPLETE', 'INCOMPLETE', 'OVERFLOW', 'SYMLINK', 'DIRECTORY',
         'FIFO_NO_WRITER', 'FIFO_LIVE_WRITER')
DEADLINE_NS = 1_000_000_000
SOURCE_PATHS = ('experiment.py', 'audit.py', 'test_audit.py', 'upstream/reader.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    return {p: sha((ROOT / p).read_bytes()) for p in SOURCE_PATHS}


def emit(value):
    print(json.dumps(value, sort_keys=True, separators=(',', ':')), flush=True)


def guarded_read(path, request, trace):
    bound = request['max_bytes']
    if type(bound) is not int or not 1 <= bound <= 67108864:
        raise ValueError('INVALID_READ_BOUND')
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        trace['opened'] = {'mode': info.st_mode, 'dev': info.st_dev, 'ino': info.st_ino}
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('NON_REGULAR_INPUT')
        parts, remaining = [], bound + 1
        while remaining:
            part = os.read(fd, remaining)
            if not part:
                break
            parts.append(part)
            remaining -= len(part)
        data = b''.join(parts)
        trace['snapshot_bytes'] = len(data)
        trace['snapshot_sha256'] = sha(data)
    finally:
        os.close(fd)
        trace['fd_closed'] = True
    if len(data) > bound:
        raise ValueError('STREAM_READ_BOUND_EXCEEDED')
    with tempfile.NamedTemporaryFile(prefix='issue3947-snapshot-') as snapshot:
        snapshot.write(data)
        snapshot.flush()
        return read_pending(snapshot.name, **request)


def worker(path, policy, request):
    emit({'phase': 'ready', 'pid': os.getpid(), 'ns': time.monotonic_ns(), 'sources': sources()})
    if sys.stdin.readline() != 'GO\n':
        raise RuntimeError('MISSING_GO')
    result = {'phase': 'result', 'pid': os.getpid(), 'start_ns': time.monotonic_ns(), 'trace': {}}
    try:
        result['receipt'] = (read_pending(path, **request) if policy == 'EXACT_READER'
                             else guarded_read(path, request, result['trace']))
    except (ValueError, OSError) as exc:
        result['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    result['end_ns'] = time.monotonic_ns()
    emit(result)


def writer(path):
    # Parent temporarily holds a Linux RDWR anchor, then closes it before GO.
    fd = os.open(path, os.O_WRONLY | os.O_CLOEXEC)
    info = os.fstat(fd)
    emit({'phase': 'writer_ready', 'pid': os.getpid(), 'ns': time.monotonic_ns(),
          'mode': info.st_mode, 'dev': info.st_dev, 'ino': info.st_ino, 'bytes_written': 0})
    try:
        if sys.stdin.readline() != 'STOP\n':
            raise RuntimeError('MISSING_WRITER_STOP')
    finally:
        os.close(fd)
    emit({'phase': 'writer_closed', 'pid': os.getpid(), 'ns': time.monotonic_ns(), 'bytes_written': 0})


def receive(proc, deadline_ns):
    """One JSON line, with a real external deadline and a bounded protocol buffer."""
    data = b''
    while b'\n' not in data:
        remaining = (deadline_ns - time.monotonic_ns()) / 1e9
        if remaining <= 0 or not select.select([proc.stdout], [], [], remaining)[0]:
            return None
        chunk = os.read(proc.stdout.fileno(), 8192)
        if not chunk:
            raise RuntimeError('CHILD_EOF_BEFORE_LINE')
        data += chunk
        if len(data) > 65536:
            raise RuntimeError('PROTOCOL_BOUND_EXCEEDED')
    if data.count(b'\n') != 1 or not data.endswith(b'\n'):
        raise RuntimeError('UNEXPECTED_EXTRA_PROTOCOL_BYTES')
    return data.decode('utf-8')


def launch(args):
    return subprocess.Popen([sys.executable, '-B', str(ROOT / 'experiment.py'), *args],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)


def stop_owned(proc):
    if proc.poll() is None:
        proc.terminate()
    try:
        return proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.communicate(timeout=2)


def fixture(folder, case):
    records = [{'delivery_id': f'delivery:{n}', 'event': 'fixture', 'value': n} for n in (1, 2, 3)]
    lines = [(json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n').encode() for x in records]
    data = b''.join(lines)
    if case == 'INCOMPLETE':
        data = data[:-1]
    elif case == 'OVERFLOW':
        data += b' ' * 600
    path = folder / 'input'
    if case.startswith('FIFO_'):
        os.mkfifo(path, 0o600)
        data = None
    elif case == 'DIRECTORY':
        path.mkdir()
        data = None
    elif case == 'SYMLINK':
        (folder / 'target').write_bytes(data)
        path.symlink_to('target')
    else:
        path.write_bytes(data)
    info = path.stat()
    return path, data, {'mode': info.st_mode, 'dev': info.st_dev, 'ino': info.st_ino,
                        'lmode': path.lstat().st_mode}


def run_case(folder, rep, case, policy):
    folder.mkdir()
    path, data, identity = fixture(folder, case)
    request = {'stream_id': 'issue3947-fixed-lifetime', 'max_records': 32, 'max_bytes': 512}
    row = {'rep': rep, 'case': case, 'policy': policy, 'request': request, 'identity': identity,
           'input_b64': None if data is None else base64.b64encode(data).decode(),
           'writer': None, 'deadline_ns': DEADLINE_NS}
    children = []
    anchor = None
    try:
        if case == 'FIFO_LIVE_WRITER':
            anchor = os.open(path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)
            peer = launch(['writer', str(path)])
            children.append(peer)
            raw_ready = receive(peer, time.monotonic_ns() + 5_000_000_000)
            if raw_ready is None:
                raise RuntimeError('WRITER_READY_TIMEOUT')
            os.close(anchor)
            anchor = None
            row['writer'] = {'ready_raw': raw_ready, 'pid': peer.pid,
                             'anchor_closed_ns': time.monotonic_ns()}
        proc = launch(['worker', str(path), policy, json.dumps(request)])
        children.append(proc)
        row['command'] = proc.args
        row['pid'] = proc.pid
        row['ready_raw'] = receive(proc, time.monotonic_ns() + 5_000_000_000)
        if row['ready_raw'] is None:
            raise RuntimeError('READER_READY_TIMEOUT')
        row['ready_received_ns'] = time.monotonic_ns()
        row['go_ns'] = time.monotonic_ns()
        proc.stdin.write(b'GO\n')
        proc.stdin.flush()
        row['response_raw'] = receive(proc, row['go_ns'] + DEADLINE_NS)
        row['observed_ns'] = time.monotonic_ns()
        row['alive_at_deadline'] = proc.poll() is None if row['response_raw'] is None else None
        row['outcome'] = 'TIMEOUT' if row['response_raw'] is None else 'RESPONSE'
        if row['response_raw'] is None:
            row['cleanup_method'] = 'SIGTERM'
            extra, error = stop_owned(proc)
        else:
            row['cleanup_method'] = 'NORMAL_EXIT'
            extra, error = proc.communicate(timeout=2)
        row.update(exit_code=proc.returncode, extra_stdout=extra.decode(), stderr=error.decode(),
                   reaped_ns=time.monotonic_ns(), reaped=proc.poll() is not None)
        if row['writer'] is not None:
            row['writer']['alive_during_read'] = peer.poll() is None
            peer.stdin.write(b'STOP\n')
            peer.stdin.flush()
            tail, err = peer.communicate(timeout=2)
            row['writer'].update(closed_raw=tail.decode(), stderr=err.decode(),
                                 exit_code=peer.returncode, reaped=peer.poll() is not None)
        row['input_unchanged'] = data is None or path.read_bytes() == data
        row['identity_after'] = {'mode': path.stat().st_mode, 'dev': path.stat().st_dev,
                                 'ino': path.stat().st_ino, 'lmode': path.lstat().st_mode}
        (folder / 'row.json').write_text(json.dumps(row, sort_keys=True) + '\n')
        return row
    finally:
        if anchor is not None:
            os.close(anchor)
        for child in children:
            if child.poll() is None:
                stop_owned(child)


def run(output, formal):
    output.mkdir(exist_ok=False)
    initial = sources()
    payload = {'schema': 'issue3947-raw-v1', 'formal': formal, 'source_sha256': initial,
               'started_ns': time.monotonic_ns(), 'rows': [], 'status': 'RUNNING'}
    try:
        for rep in range(3 if formal else 1):
            for index, case in enumerate(CASES):
                arms = POLICIES if (rep + index) % 2 == 0 else POLICIES[::-1]
                for policy in arms:
                    payload['rows'].append(run_case(output / f'{rep}-{case}-{policy}', rep, case, policy))
                    (output / 'partial.json').write_text(json.dumps(payload, sort_keys=True) + '\n')
        payload['source_sha256_after'] = sources()
        if initial != payload['source_sha256_after']:
            raise RuntimeError('SOURCE_CHANGED')
        payload['status'] = 'COMPLETE'
    except Exception as exc:
        payload.update(status='STOP_INFRASTRUCTURE', stop_type=type(exc).__name__, stop_reason=str(exc))
        raise
    finally:
        payload['ended_ns'] = time.monotonic_ns()
        (output / 'RAW.json').write_text(json.dumps(payload, sort_keys=True, separators=(',', ':')) + '\n')
    emit({'status': payload['status'], 'rows': len(payload['rows']), 'raw_sha256': sha((output / 'RAW.json').read_bytes())})


if __name__ == '__main__':
    if sys.argv[1] == 'worker':
        worker(sys.argv[2], sys.argv[3], json.loads(sys.argv[4]))
    elif sys.argv[1] == 'writer':
        writer(sys.argv[2])
    elif sys.argv[1] == 'run':
        if sys.argv[3] not in ('formal', 'construction'):
            raise ValueError('EXPECTED_MODE')
        run(Path(sys.argv[2]), sys.argv[3] == 'formal')
    else:
        raise ValueError('UNKNOWN_COMMAND')
