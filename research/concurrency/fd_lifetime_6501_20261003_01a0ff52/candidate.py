"""One frozen Linux FD-lifetime matrix; no production imports or autoexecution."""
import datetime
import errno
import hashlib
import json
import os
import pathlib
import platform
import stat
import sys
import threading
import time

from ownership import OnceOwner

ROOT = pathlib.Path(__file__).resolve().parent
INPUT = json.loads((ROOT / 'input.json').read_bytes())


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def identity(fd):
    try:
        value = os.fstat(fd)
    except OSError as exc:
        if exc.errno != errno.EBADF:
            raise
        return {'state': 'closed', 'errno': exc.errno}
    return {'state': 'open', 'device': value.st_dev, 'inode': value.st_ino,
            'kind': stat.S_IFMT(value.st_mode)}


def proc(tid):
    root = pathlib.Path('/proc/self/task') / str(tid)
    fields = (root / 'syscall').read_text().split()
    return {'tid': tid, 'state': (root / 'stat').read_text().rsplit(')', 1)[1].split()[0],
            'wchan': (root / 'wchan').read_text().strip(),
            'syscall_nr': None if fields[0] == 'running' else int(fields[0]),
            'fd': int(fields[1], 16) if len(fields) > 1 else None}


def environment():
    exe = pathlib.Path(sys.executable).resolve()
    module = pathlib.Path(threading.__file__)
    return {'python': platform.python_version(), 'machine': platform.machine(),
            'system': platform.system(), 'kernel': platform.release(),
            'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
            'threading_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
            'cpu_max': pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
            'memory_max': pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip()}


def trial(policy, schedule):
    events = []
    event_lock = threading.RLock()
    started = threading.Event()
    worker_finished = threading.Event()
    worker_info = {}
    r, w = os.pipe()
    sr, sw = os.pipe()
    original = identity(r)
    sentinel = identity(sr)
    owner = OnceOwner(r)
    replacement_created = False
    failure = None
    observed = None

    def emit(kind, actor='caller', **data):
        with event_lock:
            events.append({'seq': len(events), 'kind': kind, 'actor': actor,
                           'native_tid': threading.get_native_id(), **data})

    def close_original(actor):
        fd = r if policy == 'integer_copies' else owner.take_for_close()
        emit('close_claim', actor, claimed=fd is not None, fd=fd)
        if fd is None:
            return
        before = identity(fd)
        emit('close_requested', actor, fd=fd, identity=before)
        try:
            os.close(fd)
        except OSError as exc:
            emit('close_return', actor, fd=fd, status='error', errno=exc.errno)
            raise
        emit('close_return', actor, fd=fd, status='closed', errno=None)

    def reader():
        worker_info['tid'] = threading.get_native_id()
        emit('worker_enter', 'worker', fd=r)
        started.set()
        try:
            data = os.read(r, 1)
            worker_info['hex'] = data.hex()
            emit('read_return', 'worker', fd=r, hex=data.hex())
        except BaseException as exc:
            worker_info['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
            emit('worker_failure', 'worker', **worker_info['failure'])
        finally:
            try:
                close_original('worker')
            except BaseException as exc:
                worker_info['cleanup_failure'] = {'type': type(exc).__name__, 'message': str(exc)}
                emit('worker_cleanup_failure', 'worker', **worker_info['cleanup_failure'])
            emit('worker_exit', 'worker')
            worker_finished.set()

    thread = threading.Thread(target=reader, name='fd-lifetime-reader', daemon=True)

    def blocked(label):
        deadline = time.monotonic() + INPUT['per_boundary_timeout_seconds']
        while time.monotonic() < deadline:
            if 'tid' in worker_info:
                value = proc(worker_info['tid'])
                expected = INPUT['blocked_witness']
                if all(value[key] == expected[key] for key in ('syscall_nr', 'state', 'wchan')) and value['fd'] == r:
                    emit('blocked_observed', label=label, observation=value)
                    return
            time.sleep(0.001)
        raise RuntimeError('STOP: missing frozen blocked witness ' + label)

    def write(fd, byte, purpose):
        emit('write_requested', fd=fd, hex=byte.hex(), purpose=purpose)
        count = os.write(fd, byte)
        emit('write_return', fd=fd, count=count, purpose=purpose)
        if count != 1:
            raise RuntimeError('STOP: one-byte write incomplete')

    def join_worker():
        if not worker_finished.wait(INPUT['per_boundary_timeout_seconds']):
            raise RuntimeError('STOP: worker did not finish')
        thread.join(INPUT['per_boundary_timeout_seconds'])
        if thread.is_alive():
            raise RuntimeError('STOP: native worker did not join')
        deadline = time.monotonic() + INPUT['per_boundary_timeout_seconds']
        while (pathlib.Path('/proc/self/task') / str(worker_info['tid'])).exists() and time.monotonic() < deadline:
            time.sleep(0.001)
        if (pathlib.Path('/proc/self/task') / str(worker_info['tid'])).exists():
            raise RuntimeError('STOP: joined worker proc entry remained')
        emit('thread_joined', tid=worker_info['tid'], proc_absent=not (pathlib.Path('/proc/self/task') / str(worker_info['tid'])).exists())

    def reuse():
        nonlocal replacement_created
        if identity(r)['state'] != 'closed':
            raise RuntimeError('STOP: reuse slot not closed')
        emit('dup2_requested', source_fd=sr, target_fd=r, source_identity=identity(sr))
        value = os.dup2(sr, r, inheritable=False)
        emit('dup2_return', source_fd=sr, target_fd=r, returned_fd=value, replacement_identity=identity(r))
        if value != r or identity(r) != sentinel:
            raise RuntimeError('STOP: replacement identity mismatch')
        os.close(sr)
        emit('alias_closed', fd=sr)
        replacement_created = True
        write(sw, bytes.fromhex(INPUT['replacement_hex']), 'replacement_data')

    emit('row_open', original_fd=r, original_write_fd=w, sentinel_fd=sr,
         sentinel_write_fd=sw, original_identity=original, sentinel_identity=sentinel)
    try:
        thread.start()
        if not started.wait(INPUT['per_boundary_timeout_seconds']):
            raise RuntimeError('STOP: worker not started')
        blocked('before_action')
        if schedule == 'caller_close_reuse_before_worker_finally':
            close_original('caller')
            emit('caller_close_checkpoint', slot_identity=identity(r), worker_done=worker_finished.is_set())
            blocked('after_caller_close')
            reuse()
            blocked('after_reuse')
            emit('reused_slot_checkpoint', slot_identity=identity(r), worker_done=worker_finished.is_set())
            write(w, bytes.fromhex(INPUT['data_hex']), 'harness_release_old_read')
            join_worker()
        else:
            write(w, bytes.fromhex(INPUT['data_hex']), 'primary_data')
            join_worker()
            if schedule == 'worker_finally_reuse_before_late_caller':
                reuse()
                close_original('caller')
            else:
                write(sw, bytes.fromhex(INPUT['replacement_hex']), 'positive_sentinel_data')
        probe_fd = r if replacement_created else sr
        os_identity = identity(probe_fd)
        if os_identity['state'] == 'open':
            os.set_blocking(probe_fd, False)
            probe = {'state': 'open', 'hex': os.read(probe_fd, 1).hex(), 'errno': None}
        else:
            try:
                os.read(probe_fd, 1)
            except OSError as exc:
                probe = {'state': 'closed', 'hex': None, 'errno': exc.errno}
            else:
                raise RuntimeError('STOP: closed sentinel unexpectedly readable')
        observed = {'probe_fd': probe_fd, 'identity': os_identity, 'probe': probe,
                    'worker_hex': worker_info.get('hex'), 'worker_done': worker_finished.is_set(),
                    'thread_alive': thread.is_alive()}
        emit('primary_checkpoint', state=observed)
    except BaseException as exc:
        failure = {'type': type(exc).__name__, 'message': str(exc)}
        emit('row_failure', **failure)
    finally:
        if thread.is_alive():
            try:
                write(w, bytes.fromhex(INPUT['data_hex']), 'emergency_release')
                join_worker()
            except BaseException as exc:
                emit('emergency_cleanup_failure', type=type(exc).__name__, message=str(exc))
        for fd in sorted({r, w, sr, sw}):
            before = identity(fd)
            if before['state'] == 'open':
                os.close(fd)
                emit('harness_closed', fd=fd, identity=before)
        final = {str(fd): identity(fd) for fd in sorted({r, w, sr, sw})}
        emit('final_checkpoint', fds=final, thread_alive=thread.is_alive(),
             proc_absent='tid' in worker_info and not (pathlib.Path('/proc/self/task') / str(worker_info['tid'])).exists())
    return {'policy': policy, 'schedule': schedule, 'failure': failure,
            'worker_failure': worker_info.get('failure'), 'worker_cleanup_failure': worker_info.get('cleanup_failure'),
            'events': events, 'primary': observed, 'final': final}


def main():
    out = pathlib.Path(sys.argv[1])
    handle = out.open('xb')
    total = 0
    def append(value):
        nonlocal total
        encoded = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
        total += len(encoded)
        if total > INPUT['raw_byte_cap']:
            raise RuntimeError('STOP: raw byte cap exceeded')
        handle.write(encoded)
        handle.flush()
    append({'kind': 'header', 'allocation': INPUT['allocation'], 'started_utc': utc(),
            'input_sha256': hashlib.sha256((ROOT / 'input.json').read_bytes()).hexdigest(),
            'environment': environment()})
    completed = 0
    try:
        for policy in INPUT['policies']:
            for schedule in INPUT['schedules']:
                row = trial(policy, schedule)
                append({'kind': 'row', **row})
                completed += 1
                if row['failure'] or row['worker_failure'] or row['worker_cleanup_failure']:
                    raise RuntimeError('STOP: first row construction failure')
        append({'kind': 'footer', 'allocation': INPUT['allocation'], 'ended_utc': utc(), 'rows': completed})
    finally:
        handle.close()
    print(json.dumps({'rows': completed, 'raw_bytes': total}))


if __name__ == '__main__':
    main()
