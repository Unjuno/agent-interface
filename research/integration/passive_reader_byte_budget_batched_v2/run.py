"""Finite Issue 3977 file/CLI experiment. No network, model, GUI or shared writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ENV = {'PATH': os.defpath, 'PYTHONPATH': str(ROOT),
       'PYTHONDONTWRITEBYTECODE': '1', 'LC_ALL': 'C.UTF-8'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def writer(path, total):
    from upstream.ledger import DeliveryLedger
    ledger = DeliveryLedger()
    a = ledger.prepare({'event': 'notification', 'message': 'first'})
    b = ledger.prepare({'event': 'notification', 'message': 'second'})
    c = ledger.prepare({'event': 'notification', 'message': ''})
    prefix = encode(a) + encode(b)
    padding = total - len(prefix) - len(encode(c))
    if padding < 0:
        raise ValueError('NEGATIVE_PADDING')
    c['message'] = 'x' * padding
    suffix = encode(c)
    with path.open('xb') as f:
        f.write(prefix)
        f.flush()
    print(json.dumps({'phase': 'PREFIX', 'pid': os.getpid(), 'bytes': len(prefix),
                      'sha256': sha(prefix)}), flush=True)
    if sys.stdin.readline() != 'APPEND\n':
        raise ValueError('EXPECTED_APPEND')
    with path.open('ab') as f:
        f.write(suffix)
        f.flush()
    print(json.dumps({'phase': 'APPENDED', 'pid': os.getpid(), 'bytes': len(prefix+suffix),
                      'sha256': sha(prefix+suffix)}), flush=True)
    if sys.stdin.readline() != 'STOP\n':
        raise ValueError('EXPECTED_STOP')


def receive(proc):
    with selectors.DefaultSelector() as selector:
        selector.register(proc.stdout, selectors.EVENT_READ)
        if not selector.select(3):
            raise TimeoutError('WRITER_ACK_TIMEOUT')
        line = proc.stdout.readline()
    if not line.endswith(b'\n'):
        raise ValueError('WRITER_ACK_FRAMING')
    json.loads(line)
    return line


def call(case, name, stream, sid, bound, limit, cursor=None):
    cmd = [sys.executable, '-B', '-m', 'upstream', '--stream', str(stream),
           '--stream-id', sid, '--max-bytes', str(bound), '--max-records', str(limit)]
    if cursor is not None:
        cmd += ['--cursor', str(cursor)]
    record = {'name': name, 'argv': cmd, 'bound': bound, 'limit': limit,
              'cursor_file': None if cursor is None else cursor.name,
              'stream_file': stream.name}
    put(case / (name+'.command.json'), record)
    completed = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, timeout=3)
    (case/(name+'.stdout')).write_bytes(completed.stdout)
    (case/(name+'.stderr')).write_bytes(completed.stderr)
    record['exit'] = completed.returncode
    put(case/(name+'.exit.json'), record)
    if completed.returncode not in (0, 2) or completed.stderr:
        raise RuntimeError('UNEXPECTED_CLI_PROCESS_RESULT')
    value = json.loads(completed.stdout)
    return record, value


def one(out, index, total, limit, repetition):
    case = out / f'case-{index:02d}'
    case.mkdir()
    stream = case/'stream.jsonl'
    sid = f'budget-{index:02d}'
    row = {'index': index, 'total': total, 'limit': limit, 'repetition': repetition,
           'stream_id': sid, 'case': case.name, 'calls': []}
    cmd = [sys.executable, '-B', str(ROOT/'run.py'), 'writer', str(stream), str(total)]
    row['writer_argv'] = cmd
    err = (case/'writer.stderr').open('wb')
    proc = subprocess.Popen(cmd, cwd=ROOT, env=ENV, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=err)
    row['writer_pid'] = proc.pid
    try:
        ack = receive(proc)
        (case/'writer-prefix.stdout').write_bytes(ack)
        prefix = stream.read_bytes()
        (case/'prefix.jsonl').write_bytes(prefix)
        rec, value = call(case, 'prefix', stream, sid, 1024, 32)
        row['calls'].append(rec)
        put(case/'cursor.json', value['next_cursor'])
        proc.stdin.write(b'APPEND\n'); proc.stdin.flush()
        ack = receive(proc)
        (case/'writer-append.stdout').write_bytes(ack)
        for name, bound, count, cursor in [
                ('fixed', 1024, limit, case/'cursor.json'),
                ('repeat', 1024, limit, case/'cursor.json'),
                ('expanded', 2048, limit, case/'cursor.json')]:
            rec, value = call(case, name, stream, sid, bound, count, cursor)
            row['calls'].append(rec)
        put(case/'advanced.json', value['next_cursor'])
        rec, _ = call(case, 'empty', stream, sid, 2048, limit, case/'advanced.json')
        row['calls'].append(rec)
        rec, _ = call(case, 'reset', stream, sid, 2048, 32)
        row['calls'].append(rec)
        altered = stream.read_bytes().replace(b'first', b'FIRST', 1)
        (case/'changed.jsonl').write_bytes(altered)
        rec, _ = call(case, 'changed', case/'changed.jsonl', sid, 2048, limit, case/'cursor.json')
        row['calls'].append(rec)
        proc.stdin.write(b'STOP\n'); proc.stdin.flush()
        proc.stdin.close()
        row['writer_exit'] = proc.wait(timeout=3)
        row['writer_trailing_stdout'] = proc.stdout.read().decode()
        if row['writer_exit'] != 0:
            raise RuntimeError('WRITER_NONZERO')
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(timeout=1)
        proc.stdout.close()
        if not proc.stdin.closed:
            proc.stdin.close()
        err.close()
        row['observed_cleanup_exit'] = proc.returncode
        put(case/'ROW.json', row)
    return row


def run(out, mode):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    plan = ([(1024, 1, 0), (1025, 1, 0)] if mode == 'construction' else
            [(size, limit, rep) for rep in range(2) for size in (1023, 1024, 1025)
             for limit in (1, 32)])
    rows = []
    put(out/'START.json', {'mode': mode, 'plan': plan, 'argv': sys.argv,
                          'pid': os.getpid(), 'formal_retry_count': 0})
    try:
        for i, (size, limit, rep) in enumerate(plan):
            rows.append(one(out, i, size, limit, rep))
            put(out/'ROWS.json', rows)
        put(out/'TERMINAL.json', {'status': 'COMPLETE', 'rows': len(rows),
                                  'pid': os.getpid(), 'mode': mode})
    except BaseException as error:
        put(out/'STOP.json', {'type': type(error).__name__, 'message': str(error),
                              'complete_rows': len(rows)})
        raise
    finally:
        hashes = {str(p.relative_to(out)): sha(p.read_bytes())
                  for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
        put(out/'MANIFEST.json', hashes)
    print(json.dumps({'mode': mode, 'rows': len(rows), 'status': 'COMPLETE'}))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'writer':
        writer(Path(sys.argv[2]), int(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('--out', type=Path, required=True)
        parser.add_argument('--mode', choices=('construction', 'formal'), required=True)
        parser.add_argument('--freeze', type=Path)
        args = parser.parse_args()
        if args.mode == 'formal':
            if args.freeze is None:
                raise ValueError('FORMAL_REQUIRES_FREEZE')
            frozen = json.loads(args.freeze.read_bytes())
            for name, expected in frozen['sources'].items():
                if sha((ROOT/name).read_bytes()) != expected['sha256']:
                    raise ValueError('SOURCE_FREEZE_MISMATCH:'+name)
        run(args.out, args.mode)
