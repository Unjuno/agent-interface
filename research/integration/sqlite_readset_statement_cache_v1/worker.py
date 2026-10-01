"""One isolated database case, with external writer and observer processes."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import select
import subprocess
import sys
import time
from policy import Reader


def save(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def run(spec: dict, root: Path):
    root.mkdir(parents=True, exist_ok=False)
    save(root/'SPEC.json', spec)
    dbpath = root/'state.sqlite'
    db = sqlite3.connect(dbpath, isolation_level=None)
    try:
        db.execute('PRAGMA journal_mode=DELETE')
        db.execute('PRAGMA synchronous=FULL')
        for name in ('a','b','u'):
            db.execute(f'CREATE TABLE {name}(value TEXT NOT NULL, revision INTEGER NOT NULL)')
            db.execute(f'INSERT INTO {name} VALUES (?,1)', (spec['id']+':'+name+'0',))
        db.execute('CREATE VIEW current_view AS SELECT value FROM a')
        db.execute('CREATE TABLE effects(request_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    finally:
        db.close()
    calls = []
    peer_argv = [sys.executable, '-B', str(Path(__file__).with_name('peer.py')), str(dbpath)]
    peer_error = (root/'peer-process.stderr').open('wb')
    process = subprocess.Popen(peer_argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=peer_error)
    process_start=time.monotonic_ns()
    def peer(command):
        index = len(calls)
        request=json.dumps({'op_id':index,'command':command},sort_keys=True).encode()+b'\n'
        (root/f'peer-{index:02}.request').write_bytes(request)
        start = time.monotonic_ns()
        process.stdin.write(request); process.stdin.flush()
        ready,_,_=select.select([process.stdout],[],[],3)
        if not ready: raise TimeoutError('PEER_RESPONSE_TIMEOUT')
        stdout=process.stdout.readline(1048577)
        if not stdout.endswith(b'\n') or len(stdout)>1048576:
            raise RuntimeError('PEER_INCOMPLETE_OR_OVERSIZE_RESPONSE')
        (root/f'peer-{index:02}.stdout').write_bytes(stdout)
        response=json.loads(stdout)
        receipt = {'started_ns': start,'finished_ns':time.monotonic_ns(),
                   'command':command,'op_id':index,
                   'stdout_sha256':hashlib.sha256(stdout).hexdigest(),
                   'request_sha256':hashlib.sha256(request).hexdigest()}
        calls.append(receipt); save(root/'PEER_CALLS.json',calls)
        if response['op_id']!=index or response['command']!=command:
            raise RuntimeError('PEER_RESPONSE_IDENTITY')
        return response
    initial = peer('observe')
    reader = Reader(str(dbpath), spec['mode'])
    try:
        prime = reader.prepare(spec['prime_sql']) if spec['prime_sql'] else None
        preop = peer(spec['before'])
        before = peer('observe')
        prepare_start = time.monotonic_ns()
        prepared = reader.prepare(spec['sql'])
        prepare_end = time.monotonic_ns()
        # Recording publication before writer begins makes the selected order explicit.
        save(root/'PREPARED.json', prepared)
        mutation = peer(spec['after'])
        after = peer('observe')
        commit_start = time.monotonic_ns()
        commit = reader.commit(spec['id'], prepared)
        commit_end = time.monotonic_ns()
    finally:
        reader.close()
    final = peer('observe')
    terminal = peer('stop')
    process.stdin.close()
    exit_code=process.wait(timeout=3)
    process.stdout.close(); peer_error.close()
    peer_process={'argv':peer_argv,'pid':process.pid,'returncode':exit_code,
                  'started_ns':process_start,'finished_ns':time.monotonic_ns(),
                  'terminal':terminal,
                  'stderr_sha256':hashlib.sha256((root/'peer-process.stderr').read_bytes()).hexdigest()}
    save(root/'PEER_PROCESS.json',peer_process)
    if exit_code!=0:raise RuntimeError('PEER_NONZERO_EXIT')
    result = {'spec': spec, 'worker_pid': os.getpid(), 'cache_size': reader.cache_size,
              'initial': initial, 'prime': prime, 'before_operation': preop,
              'before_prepare': before, 'prepared': prepared,
              'prepare_bracket_ns': [prepare_start, prepare_end],
              'mutation': mutation, 'after_mutation': after,
              'commit_bracket_ns': [commit_start, commit_end], 'commit': commit,
              'final': final, 'peer_calls': calls, 'peer_process':peer_process,
              'database_sha256': hashlib.sha256(dbpath.read_bytes()).hexdigest(),
              'authority': 'none', 'model_calls': 0, 'gui_inputs': 0}
    save(root/'RAW.json', result)
    print(json.dumps({'id': spec['id'], 'raw_sha256': hashlib.sha256((root/'RAW.json').read_bytes()).hexdigest()}))

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('spec'); p.add_argument('out')
    a=p.parse_args()
    run(json.loads(Path(a.spec).read_text()), Path(a.out))
