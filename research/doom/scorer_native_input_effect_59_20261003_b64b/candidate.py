"""Fresh finite native-POSIX construction; never imports earlier producers."""
import argparse
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def utc():
    return datetime.now(timezone.utc).isoformat()


def runtime():
    result = {'python': sys.version, 'platform': platform.platform(),
              'machine': platform.machine(), 'pid': os.getpid(),
              'perf_counter': vars(time.get_clock_info('perf_counter'))}
    for name in ('cpu.max', 'memory.max', 'pids.max'):
        p = Path('/sys/fs/cgroup') / name
        result[name] = p.read_text().strip() if p.exists() else None
    return result


class SampleBudget(RuntimeError):
    pass


def child(case, out):
    out.mkdir()
    sys.path.insert(0, str(HERE / 'sources' / case['arm']))
    from main_thread_scorer_polling_v1 import MainThreadScorerPolling
    from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin, ScorerFileSink
    from independent_progress_clock_v2 import ProgressSample

    events = []
    samples = []
    commands = []
    owner = threading.get_ident()

    def event(kind, **kw):
        events.append({'kind': kind, 'ns': time.perf_counter_ns(),
                       'thread_id': threading.get_ident(), **kw})

    def clock():
        value = time.perf_counter_ns()
        caller = sys._getframe(1)
        events.append({'kind': 'clock', 'ns': value, 'thread_id': threading.get_ident(),
                       'caller': caller.f_code.co_name, 'line': caller.f_lineno})
        return value

    r, w = os.pipe()
    pipe_stat = os.fstat(r)
    input_bytes = bytes.fromhex(case['input_hex'])
    written = os.write(w, input_bytes)
    if written != len(input_bytes):
        raise RuntimeError('short prequeue write')
    os.close(w)
    event('prequeued', hex=input_bytes.hex(), written=written, writer_closed=True)
    stream = os.fdopen(r, 'rb')

    def wait(fd, timeout):
        if fd != r or timeout < 0:
            raise RuntimeError('invalid native wait')
        event('wait_start', timeout_s=timeout)
        ready, _, _ = select.select([fd], [], [], timeout)
        event('wait_end', ready=bool(ready))
        return bool(ready)

    def read(fd, requested):
        if fd != r:
            raise RuntimeError('wrong native pipe')
        value = os.read(fd, min(requested, case['read_limit']))
        event('read', requested=requested, limit=case['read_limit'], hex=value.hex())
        return value

    sink = ScorerFileSink(out / 'scorer')

    def sample():
        if len(samples) >= case['sample_budget']:
            event('sample_budget', completed=len(samples))
            raise SampleBudget('finite completed-sample diagnostic cap')
        event('sample_begin', index=len(samples))
        if case['sleep_ns']:
            time.sleep(case['sleep_ns'] / 1e9)
        stamp = time.perf_counter_ns()
        payload = ProgressSample(stamp, 0, 0, False, False, False)
        samples.append({'index': len(samples), 'payload_ns': stamp})
        event('sample_end', index=len(samples)-1, payload_ns=stamp)
        return payload

    def persist(receipt):
        event('sink_begin', receipt={k: v for k, v in receipt.items() if k != 'payload'})
        sink(receipt)
        event('sink_end', count=len(sink.samples))

    def command(line):
        event('command', line=line)
        commands.append(line)
        if line == 'FINISH':
            if commands != ['α', 'FINISH']:
                raise RuntimeError('unexpected command chain')
            save(out / 'effect.json', {'schema': 'disposable-finish-effect-v1',
                                     'cell_id': case['id'], 'commands': commands,
                                     'finished': True})
            event('effect_saved')
            return False
        if line != 'α':
            raise RuntimeError('unexpected command content')
        return True

    loop = MainThreadScorerPolling(sample_hz=case['sample_hz'], clock_ns=clock,
                                   wait_readable=wait, read_fn=read)
    iterator = None
    stats = None
    started = utc()
    start_ns = time.perf_counter_ns()
    disposition = 'unknown'
    error = None
    try:
        if case['adapter'] == 'polling':
            stats = vars(loop.run(r, sample_fn=sample, scorer_sink=persist,
                                  command_handler=command))
        else:
            iterator = MainThreadScorerStdin(stream, sample, persist, loop=loop)
            for line in iterator:
                if command(line) is False:
                    break
            stats = iterator.stats()
        disposition = 'finish' if commands == ['α', 'FINISH'] else 'unexpected_terminal'
    except SampleBudget as exc:
        disposition = 'sample_budget'
        error = str(exc)
        if iterator is not None:
            stats = iterator.stats()
    finally:
        stream.close()
    end_ns = time.perf_counter_ns()
    try:
        fcntl.fcntl(r, fcntl.F_GETFD)
    except OSError as exc:
        read_fd_closed = exc.errno == errno.EBADF
    else:
        read_fd_closed = False
    event('closed', read_fd_closed=read_fd_closed)
    row = {'case': case, 'runtime': runtime(), 'owner_thread': owner,
           'pipe_is_fifo': stat.S_ISFIFO(pipe_stat.st_mode), 'pipe_inode': pipe_stat.st_ino,
           'utc_start': started, 'utc_end': utc(), 'start_ns': start_ns, 'end_ns': end_ns,
           'disposition': disposition, 'error': error, 'stats': stats,
           'period_ns': loop.period_ns, 'samples': samples, 'commands': commands,
           'events': events, 'read_fd_closed': read_fd_closed}
    save(out / 'row.json', row)
    print(json.dumps({'id': case['id'], 'disposition': disposition, 'samples': len(samples)}))


def run(deck, out):
    cases = json.loads(deck.read_text())
    out.mkdir()
    started = utc()
    rows = []
    for case in cases:
        cell = out / case['id']
        argv = [sys.executable, '-B', str(HERE / 'candidate.py'), '--child',
                json.dumps(case, ensure_ascii=False), '--out', str(cell)]
        begin = utc()
        proc = subprocess.run(argv, capture_output=True, timeout=3)
        end = utc()
        if len(proc.stdout) + len(proc.stderr) > 65536:
            raise RuntimeError('child output exceeded bound')
        (out / (case['id'] + '.stdout')).write_bytes(proc.stdout)
        (out / (case['id'] + '.stderr')).write_bytes(proc.stderr)
        if proc.returncode:
            save(out / 'FIRST_CHILD_FAILURE.json', {'case': case, 'argv': argv,
                'utc_start': begin, 'utc_end': end, 'exit_code': proc.returncode})
            raise RuntimeError('child failed; preserve output and stop')
        row = json.loads((cell / 'row.json').read_text())
        row['process_receipt'] = {'argv': argv, 'utc_start': begin, 'utc_end': end,
                                  'exit_code': proc.returncode}
        row['artifacts'] = {str(f.relative_to(out)): {'sha256': sha(f.read_bytes()),
                             'bytes': len(f.read_bytes())}
                            for f in sorted(cell.rglob('*')) if f.is_file()}
        rows.append(row)
    raw = {'schema': 'native-scorer-input-59-v1', 'utc_start': started, 'utc_end': utc(),
           'runtime': runtime(), 'rows': rows}
    save(out / 'RAW.json', raw)
    if sum(f.stat().st_size for f in out.rglob('*') if f.is_file()) > 8 << 20:
        raise RuntimeError('total output exceeded bound')
    print(json.dumps({'rows': len(rows), 'dispositions': {v: sum(r['disposition'] == v for r in rows)
          for v in sorted({r['disposition'] for r in rows})}, 'raw_sha256': sha((out/'RAW.json').read_bytes())}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--deck', type=Path)
    p.add_argument('--child')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.child:
        child(json.loads(a.child), a.out)
    else:
        run(a.deck, a.out)
