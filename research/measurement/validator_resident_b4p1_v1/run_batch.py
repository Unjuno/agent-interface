"""One first-outcome batch; no retries. Warmups are retained and excluded."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import select
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
NOW = time.perf_counter_ns


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def cpu():
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return round((r.ru_utime + r.ru_stime) * 1e9)


def receive(process):
    data = bytearray()
    deadline = time.monotonic() + 5
    while not data.endswith(b'\n'):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([process.stdout], [], [], remaining)[0]:
            raise TimeoutError('response deadline')
        chunk = os.read(process.stdout.fileno(), 4096)
        if not chunk:
            raise EOFError('worker ended before complete response')
        data.extend(chunk)
        if len(data) > 16384 or b'\n' in data[:-1]:
            raise ValueError('unexpected response framing')
    return bytes(data)


def sequence(mode, count, trial, phase, work, fixtures, output):
    path = work / 'input.json'
    cmd = [sys.executable, '-I', '-S', '-B', str(ROOT / 'worker.py')]
    env = {k: v for k, v in os.environ.items()
           if not k.startswith('PYTHON') and k not in ('DISPLAY', 'WAYLAND_DISPLAY')}
    record = dict(mode=mode, count=count, trial=trial, phase=phase,
                  argv=cmd, cwd=str(work), stdin=(json.dumps(str(path))+'\n'),
                  responses=[], processes=[], status='RUNNING', affinity=sorted(os.sched_getaffinity(0)))
    process = None
    before_cpu = cpu()
    record['start_ns'] = NOW()
    try:
        for step in range(count):
            f = fixtures[step % 8]
            data = None if f['content'] is None else f['content'].encode('utf-8')
            prep_start = NOW()
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(data)
            request_start = NOW()
            if process is None:
                process = subprocess.Popen(cmd, cwd=work, env=env, stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
                record['processes'].append(dict(pid=process.pid, exit=None, stderr=None))
            pid = process.pid
            request = record['stdin'].encode('ascii')
            sent = process.stdin.write(request)
            if sent != len(request):
                raise OSError('short request write')
            received = receive(process)
            response_end = NOW()
            after = path.read_bytes() if path.exists() else None
            item = dict(step=step, fixture=step % 8, pid=pid,
                        prepare_start_ns=prep_start, request_start_ns=request_start,
                        response_end_ns=response_end, input_sha256=digest(data),
                        after_sha256=digest(after), stdout=received.decode('ascii'))
            record['responses'].append(item)
            if mode == 'fresh':
                process.stdin.close(); process.stdin = None
                tail, err = process.communicate(timeout=5)
                record['processes'][-1].update(exit=process.returncode, stderr=err.decode('utf-8'),
                                                tail=tail.decode('ascii'))
                if tail or err or process.returncode != 0:
                    raise RuntimeError('worker termination mismatch')
                process = None
        if process is not None:
            process.stdin.close(); process.stdin = None
            tail, err = process.communicate(timeout=5)
            record['processes'][-1].update(exit=process.returncode, stderr=err.decode('utf-8'),
                                            tail=tail.decode('ascii'))
            if tail or err or process.returncode != 0:
                raise RuntimeError('worker termination mismatch')
            process = None
        record['status'] = 'COMPLETE'
    except BaseException as error:
        record['status'] = 'STOP'
        record['error'] = repr(error)
        record['traceback'] = traceback.format_exc()
        if process is not None:
            if process.poll() is None:
                process.kill()
            tail, err = process.communicate(timeout=5)
            record['processes'][-1].update(exit=process.returncode, stderr=err.decode('utf-8','replace'),
                                           tail=tail.decode('ascii','replace'))
        raise
    finally:
        record['end_ns'] = NOW()
        record['children_cpu_ns'] = cpu() - before_cpu
        output.write(json.dumps(record, ensure_ascii=True, sort_keys=True)+'\n')
        output.flush()
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--count', type=int, choices=(1,8,32), required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--construction', action='store_true')
    a = p.parse_args()
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    if not a.construction:
        for path, expected in json.loads((ROOT/'FREEZE.json').read_text()).items():
            assert digest((ROOT/path).read_bytes()) == expected, path
    fixtures = json.loads((ROOT/'FIXTURES.json').read_text())
    work = a.out/'work'; work.mkdir()
    trials = [(-1, 'warmup')] if a.construction else [(-1,'warmup')]+[(i,'measured') for i in range(7)]
    with (a.out/'RAW.jsonl').open('x') as output:
        for trial,phase in trials:
            order = ['fresh','resident'] if trial % 2 == 0 else ['resident','fresh']
            for mode in order:
                sequence(mode,a.count,trial,phase,work,fixtures,output)
    print(json.dumps({'count':a.count,'sequences':2*len(trials),'complete':True},sort_keys=True))


if __name__ == '__main__':
    main()
