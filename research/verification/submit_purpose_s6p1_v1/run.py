"""One bounded allocation with first-outcome retention; no case replacement."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def execute(args, packet=None):
    raw = '' if packet is None else json.dumps(packet, sort_keys=True, separators=(',', ':'))
    started = time.monotonic_ns()
    env = {'PATH': os.environ.get('PATH', ''), 'LANG': 'C.UTF-8', 'PYTHONHASHSEED': '0', 'PYTHONDONTWRITEBYTECODE': '1'}
    proc = subprocess.Popen([sys.executable, '-S', '-B', *args], cwd=HERE, env=env,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        out, err = proc.communicate(raw.encode(), timeout=3)
    except subprocess.TimeoutExpired:
        timed_out = True; proc.kill(); out, err = proc.communicate(timeout=3)
    return {'argv': [sys.executable, '-S', '-B', *args], 'pid': proc.pid, 'exit': proc.returncode,
            'started_ns': started, 'ended_ns': time.monotonic_ns(), 'stdin': raw,
            'stdout': out.decode(), 'stderr': err.decode(), 'stdout_sha256': digest(out),
            'timed_out': timed_out}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); target = args.out.resolve(); target.mkdir(exist_ok=False)
    freeze = json.loads((HERE / 'FREEZE.json').read_text())
    for name, sha in freeze['files'].items():
        if digest((HERE / name).read_bytes()) != sha:
            raise ValueError('source drift: ' + name)
    definition = json.loads((HERE / 'SCHEDULE.json').read_text())
    schedule = [{'id': f'r{rep}-{index:02}-{policy}', 'scenario': definition['conditions'][index]['name'],
                 'packet': {'session': definition['session'], 'policy': policy, 'requests': definition['conditions'][index]['requests']}}
                for rep, index, policy in definition['order']]
    meta = {'started_ns': time.monotonic_ns(), 'pid': os.getpid(), 'planned': len(schedule),
            'freeze_sha256': digest((HERE / 'FREEZE.json').read_bytes()), 'source_hashes': freeze['files']}
    (target / 'START.json').write_text(json.dumps(meta, sort_keys=True, indent=2) + '\n')
    first_error = None; completed = 0
    for case in schedule:
        d = target / case['id']; d.mkdir(exist_ok=False)
        try:
            a = execute([str(HERE / 'actor.py'), '--db', str(d / 'store.sqlite'), '--sql', str(d / 'sql.jsonl')], case['packet'])
            (d / 'ACTOR.json').write_text(json.dumps(a, sort_keys=True, indent=2) + '\n')
            if a['exit'] != 0 or a['timed_out'] or a['stderr']:
                raise ValueError('actor termination')
            o = execute([str(HERE / 'observer.py'), str(d / 'store.sqlite')])
            (d / 'OBSERVER.json').write_text(json.dumps(o, sort_keys=True, indent=2) + '\n')
            if o['exit'] != 0 or o['timed_out'] or o['stderr']:
                raise ValueError('observer termination')
            completed += 1
            (target / 'PROGRESS.json').write_text(json.dumps({'complete': completed, 'last': case['id']}) + '\n')
            if time.monotonic_ns() - meta['started_ns'] > 60_000_000_000:
                raise TimeoutError('allocation bound')
        except Exception as error:
            first_error = repr(error); break
    ending = {'ended_ns': time.monotonic_ns(), 'pid': os.getpid(), 'complete': completed,
              'planned': len(schedule), 'error': first_error, 'disposition': 'COMPLETE' if first_error is None else 'STOP'}
    (target / 'END.json').write_text(json.dumps(ending, sort_keys=True, indent=2) + '\n')
    print(json.dumps(ending, sort_keys=True))
    return 0 if first_error is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
