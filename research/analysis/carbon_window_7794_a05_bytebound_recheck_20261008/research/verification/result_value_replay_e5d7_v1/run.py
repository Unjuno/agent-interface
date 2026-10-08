"""One exclusive batch of disposable subprocess counter trials; never resumes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
SCENARIOS = ('STABLE', 'OTHER_EFFECT', 'ABA', 'LOST_REPLY', 'PAYLOAD_CONFLICT', 'NEW_OPERATION')
POLICIES = ('CURRENT_PROJECTION', 'RECORDED_RESULT')


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commands(scenario):
    seq = [('A', 1)]
    if scenario in ('OTHER_EFFECT', 'ABA', 'LOST_REPLY', 'NEW_OPERATION'):
        seq.append(('B', 3))
    if scenario == 'ABA':
        seq.append(('C', -3))
    if scenario == 'NEW_OPERATION':
        seq.append(('D', 2))
    probe = ('D', 2) if scenario == 'NEW_OPERATION' else ('A', 2 if scenario == 'PAYLOAD_CONFLICT' else 1)
    return seq + [probe, probe]


def run_case(root, scenario, policy, rep):
    root.mkdir()
    dbpath = root / 'state.sqlite'
    db = sqlite3.connect(dbpath, isolation_level=None)
    db.execute('PRAGMA journal_mode=DELETE')
    db.executescript('CREATE TABLE state(singleton INTEGER PRIMARY KEY, counter INTEGER, version INTEGER);'
                     'CREATE TABLE effects(operation_id TEXT PRIMARY KEY,delta INTEGER,counter_after INTEGER,commit_version INTEGER UNIQUE);'
                     'INSERT INTO state VALUES(1,0,0);')
    db.close()
    shutil.copyfile(dbpath, root / 'initial.sqlite')
    rows = []
    for index, (opid, delta) in enumerate(commands(scenario)):
        request = {'scope': 'e5d7-private', 'operation_id': opid, 'delta': delta}
        prefix = root / f'{index:02d}'
        request_text = json.dumps(request, sort_keys=True) + '\n'
        prefix.with_suffix('.request.json').write_text(request_text)
        crash = scenario == 'LOST_REPLY' and index == 0
        argv = [sys.executable, '-S', '-B', str(ROOT / 'receiver.py'), '--db', str(dbpath), '--policy', policy]
        if crash:
            argv.append('--crash')
        started = time.monotonic_ns()
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = proc.communicate(request_text, timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
            prefix.with_suffix('.stdout').write_text(out)
            prefix.with_suffix('.stderr').write_text(err)
            save(prefix.with_suffix('.process.json'), {'argv': argv, 'pid': proc.pid, 'returncode': proc.returncode, 'stop': 'TIMEOUT'})
            raise RuntimeError('owned_receiver_timeout')
        ended = time.monotonic_ns()
        prefix.with_suffix('.stdout').write_text(out)
        prefix.with_suffix('.stderr').write_text(err)
        snap = prefix.with_suffix('.sqlite')
        shutil.copyfile(dbpath, snap)
        receipt = {'argv': argv, 'pid': proc.pid, 'returncode': proc.returncode, 'started_ns': started,
                   'ended_ns': ended, 'snapshot': snap.name, 'snapshot_sha256': digest(snap)}
        save(prefix.with_suffix('.process.json'), receipt)
        rows.append({'index': index, 'prefix': prefix.name, 'request': request, **receipt})
        save(root / 'case.json', {'scenario': scenario, 'policy': policy, 'rep': rep, 'calls': rows})
        if proc.returncode != (73 if crash else 0):
            raise RuntimeError('unexpected_receiver_exit')
    return {'case': root.name, 'scenario': scenario, 'policy': policy, 'rep': rep, 'calls': len(rows)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--scenario', required=True, choices=SCENARIOS)
    ap.add_argument('--construction', action='store_true')
    a = ap.parse_args()
    if not a.construction:
        freeze = json.loads((ROOT / 'FREEZE.json').read_text())
        for name, expected in freeze['files'].items():
            if digest(ROOT / name) != expected:
                raise RuntimeError('source_drift:' + name)
    a.out.mkdir(parents=True, exist_ok=False)
    save(a.out / 'CONSUMED.json', {'pid': os.getpid(), 'argv': sys.argv, 'scenario': a.scenario,
                                  'phase': 'construction' if a.construction else 'formal'})
    rows = []
    try:
        for rep in (range(1) if a.construction else range(2)):
            for policy in POLICIES:
                rows.append(run_case(a.out / f'{a.scenario}-{policy}-{rep}', a.scenario, policy, rep))
        save(a.out / 'batch.json', {'status': 'COMPLETE', 'cases': rows})
        print(json.dumps({'status': 'COMPLETE', 'cases': len(rows), 'calls': sum(r['calls'] for r in rows)}))
        return 0
    except Exception as exc:
        save(a.out / 'STOP.json', {'status': 'STOP', 'error': repr(exc), 'complete_prefix': rows})
        raise


if __name__ == '__main__':
    raise SystemExit(main())
