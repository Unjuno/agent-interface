"""One bounded engineering check. Does not rerun the retained timing allocation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
SCENARIOS = ('APPEND', 'REPEAT', 'INCOMPLETE', 'BLOCKED_SEQUENCE', 'PREFIX_CHANGED', 'TOTAL_CAP')
ARMS = ('upstream', 'candidate')
MODULE = 'research.integration.event_inbox_reader_v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + '\n')


def invoke(argv, cwd, env):
    start = time.monotonic_ns()
    child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = child.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill()
        stdout, stderr = child.communicate()
        return dict(argv=argv, cwd=str(cwd), pid=child.pid, exit=child.returncode,
                    stdout=stdout.decode(), stderr=stderr.decode(), timeout=True,
                    start_ns=start, end_ns=time.monotonic_ns())
    return dict(argv=argv, cwd=str(cwd), pid=child.pid, exit=child.returncode,
                stdout=stdout.decode(), stderr=stderr.decode(), timeout=False,
                start_ns=start, end_ns=time.monotonic_ns())


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    freeze = json.loads((ROOT / 'FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError('SOURCE_MISMATCH:' + name)
    env = dict(os.environ)
    for name in ('DISPLAY', 'WAYLAND_DISPLAY', 'PYTHONPATH'):
        env.pop(name, None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    raw = dict(schema='h8m4-cli-compat-v1', freeze_sha256=digest((ROOT / 'FREEZE.json').read_bytes()),
               sources=freeze['files'], units=[], rows=[], complete=False)
    save(out / 'RAW.json', raw)
    with tempfile.TemporaryDirectory(prefix='h8m4-cli-') as temp:
        temp = Path(temp)
        roots = {}
        for arm in ARMS:
            root = temp / arm
            package = root / 'research/integration/event_inbox_reader_v1'
            package.mkdir(parents=True)
            for source, target in ((arm + '_reader.py', 'reader.py'), ('cli.py', '__main__.py'),
                                   ('test_cli.py', 'test_cli.py'), ('test_reader.py', 'test_reader.py')):
                shutil.copyfile(ROOT / 'source' / source, package / target)
            ledger = root / 'research/live_control/delivery_ledger_v2.py'
            ledger.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'source/delivery_ledger_v2.py', ledger)
            roots[arm] = root
            unit = invoke([sys.executable, '-S', '-B', '-m', 'unittest', '-v',
                           MODULE + '.test_reader', MODULE + '.test_cli'], root, env)
            unit['arm'] = arm
            raw['units'].append(unit)
            save(out / 'RAW.json', raw)
            if unit['exit'] != 0 or unit['timeout']:
                return 2
        first = b'{"event":"ready","delivery_id":"delivery:1"}\n'
        second = '{"event":"notice","delivery_id":"delivery:2","text":"保存"}\n'.encode()
        for scenario in SCENARIOS:
            folder = temp / scenario
            folder.mkdir()
            stream, cursor_path = folder / 'stream.jsonl', folder / 'cursor.json'
            current_cursor = None
            first_cursor = None
            data = first + second if scenario == 'REPEAT' else first
            for phase in range(3):
                if phase == 1:
                    if scenario in ('APPEND', 'TOTAL_CAP'):
                        data = first + second
                    elif scenario == 'INCOMPLETE':
                        data = first + second[:-1]
                    elif scenario == 'BLOCKED_SEQUENCE':
                        data = first + second.replace(b'delivery:2', b'delivery:1')
                    elif scenario == 'PREFIX_CHANGED':
                        data = first.replace(b'ready', b'other')
                elif phase == 2:
                    if scenario == 'INCOMPLETE':
                        data += b'\n'
                    if scenario == 'REPEAT':
                        current_cursor = first_cursor
                stream.write_bytes(data)
                cursor_text = None if current_cursor is None else json.dumps(current_cursor, sort_keys=True) + '\n'
                if cursor_text is not None:
                    cursor_path.write_text(cursor_text)
                results = []
                for arm in ARMS:
                    argv = [sys.executable, '-S', '-B', '-m', MODULE,
                            '--stream', str(stream), '--stream-id', 'h8m4-compat',
                            '--max-records', '1' if phase == 0 else '32']
                    if current_cursor is not None:
                        argv += ['--cursor', str(cursor_path)]
                    if scenario == 'TOTAL_CAP':
                        argv += ['--max-bytes', str(len(first))]
                    result = invoke(argv, roots[arm], env)
                    result.update(scenario=scenario, phase=phase, arm=arm,
                                  stream_before=data.hex(), stream_after=stream.read_bytes().hex(),
                                  cursor_before=cursor_text,
                                  cursor_after=None if cursor_text is None else cursor_path.read_text())
                    raw['rows'].append(result)
                    results.append(result)
                    save(out / 'RAW.json', raw)
                    if result['timeout']:
                        return 2
                if any(r['exit'] not in (0, 2) or r['stderr'] for r in results):
                    return 2
                a, b = [json.loads(r['stdout']) for r in results]
                if a != b:
                    return 1
                current_cursor = a.get('next_cursor', current_cursor)
                if phase == 0:
                    first_cursor = current_cursor
        raw['complete'] = True
        save(out / 'RAW.json', raw)
    print(json.dumps({'rows': len(raw['rows']), 'unit_runs': len(raw['units']), 'complete': True}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
