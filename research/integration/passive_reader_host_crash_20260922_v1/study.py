"""Issue #3931: isolated host-persistence process-crash experiment, no input/ACK.

The off-path supervisor keeps audit bytes. Recovery sees ONLY its own store;
therefore 'lost' means unavailable to that host via store + current read cursor,
not destruction of the immutable source/audit corpus. No production integration.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
POLICIES = ('cursor_first', 'response_first', 'atomic')
CUTS = ('before', 'after_first', 'after_second', 'after_commit', 'normal')
READER_BLOB = 'ea72c166c2cea511ea91031dfbb14563fe4e3245'


def encode(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def durable(path, obj):
    """Atomic individual file publication, not a multi-file transaction."""
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('xb') as f:
        f.write(encode(obj)); f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def db_open(root):
    con = sqlite3.connect(root/'store.sqlite', timeout=2)
    con.execute('PRAGMA synchronous=FULL')
    return con


def initialise(root, policy):
    if policy == 'atomic':
        with db_open(root) as con:
            con.execute('PRAGMA journal_mode=DELETE')
            con.execute('CREATE TABLE state (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            con.executemany('INSERT INTO state VALUES (?,?)', [('cursor','null'),('journal','[]')])
        con.close()
    else:
        durable(root/'cursor.json', None)
        durable(root/'journal.json', [])


def get_state(root, policy, con=None):
    if policy == 'atomic':
        own = con is None
        if own:
            con = db_open(root)
        try:
            return {k: json.loads(v) for k,v in con.execute('SELECT key,value FROM state')}
        finally:
            if own:
                con.close()
    return {k: json.loads((root/(k+'.json')).read_bytes()) for k in ('cursor','journal')}


def worker(root, policy, cut, stream):
    # This is the sole candidate import: byte-verified unchanged repository reader.
    from reader import read_pending
    state = get_state(root, policy)
    response = read_pending(root/'source.jsonl', stream_id=stream, cursor=state['cursor'])
    sys.stdout.buffer.write(encode({'request_cursor': state['cursor'], 'response': response}))
    sys.stdout.buffer.flush()
    # stdout above is off-path audit telemetry, never an input to host recovery.
    def crash(point):
        if cut == point:
            os._exit(73)
    crash('before')
    journal = state['journal'] + response['records']
    cursor = response['next_cursor']
    if policy == 'atomic':
        con = db_open(root)
        con.execute('BEGIN IMMEDIATE')
        con.execute('UPDATE state SET value=? WHERE key=?', (encode(journal).decode(),'journal'))
        crash('after_first')
        con.execute('UPDATE state SET value=? WHERE key=?', (encode(cursor).decode(),'cursor'))
        crash('after_second')
        con.commit()
        crash('after_commit')
        con.close()
    else:
        values = {'journal':journal, 'cursor':cursor}
        order = ('cursor','journal') if policy == 'cursor_first' else ('journal','cursor')
        for key, point in zip(order, ('after_first','after_second')):
            durable(root/(key+'.json'), values[key])
            crash(point)
        crash('after_commit')
    return 0


def snapshot(root, policy):
    # Fresh independent connection performs SQLite's ordinary recovery if needed.
    # Retain pre-open identities too; no business-level reconstruction occurs here.
    before = {p.name: digest(p.read_bytes()) for p in sorted(root.glob('store.sqlite*'))}
    state = get_state(root, policy)
    names = ['store.sqlite'] if policy == 'atomic' else ['cursor.json','journal.json']
    blobs = {name: base64.b64encode((root/name).read_bytes()).decode() for name in names}
    return {'state':state, 'files_b64':blobs, 'pre_observer_sqlite_sha256':before}


def invocation(root, policy, cut, stream):
    args = [sys.executable, str(HERE/'study.py'), 'worker', '--out', str(root),
            '--policy', policy, '--cut',cut,'--stream',stream]
    p = subprocess.run(args, capture_output=True, timeout=8,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    return {'command':args, 'returncode':p.returncode,
            'stdout_b64':base64.b64encode(p.stdout).decode(),
            'stderr_b64':base64.b64encode(p.stderr).decode()}


def source_hashes():
    return {name:digest((HERE/name).read_bytes()) for name in ('reader.py','study.py','audit.py')}


def environment():
    return {'python':sys.version, 'executable':sys.executable,
            'executable_sha256':digest(Path(sys.executable).read_bytes()),
            'sqlite':sqlite3.sqlite_version, 'platform':platform.platform(),
            'docker_cli':shutil.which('docker'), 'engine':'provided Linux execution container',
            'image_digest':None, 'clock':'time.time_ns only records provenance, no timing claim'}


def verify_reader():
    b = (HERE/'reader.py').read_bytes()
    actual = hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    if actual != READER_BLOB:
        raise RuntimeError('STOP_READER_BLOB_MISMATCH')


def run(root, allocation, mode):
    verify_reader()
    freeze = json.loads((HERE/'FREEZE.json').read_bytes()) if mode == 'formal' else None
    if freeze is not None:
        if freeze['source_sha256'] != source_hashes() or freeze['environment'] != environment():
            raise RuntimeError('STOP_FROZEN_SOURCE_OR_ENVIRONMENT_MISMATCH')
        if freeze['allocation'] != allocation:
            raise RuntimeError('STOP_ALLOCATION_ID_MISMATCH')
    root.mkdir(parents=True, exist_ok=False)
    raw = {'schema':'passive-host-crash-3931-v1', 'mode':mode, 'allocation':allocation,
           'source_sha256':source_hashes(), 'environment':environment(),
           'started_ns':time.time_ns(), 'cases':[], 'stop':None}
    repetitions = 3 if mode == 'formal' else 1
    try:
        for policy in POLICIES:
            for cut in CUTS:
                for rep in range(repetitions):
                    cid = f'{policy}-{cut}-{rep}'
                    work = root/'stores'/cid
                    work.mkdir(parents=True, exist_ok=False)
                    stream = allocation+':'+cid
                    records = [{'event':'diagnostic_notification','delivery_id':f'delivery:{i}',
                                'payload':f'{stream}:item:{i}'} for i in range(1,7)]
                    source = b''.join(encode(r) for r in records)
                    (work/'source.jsonl').write_bytes(source)
                    initialise(work, policy)
                    row = {'id':cid, 'policy':policy, 'cut':cut, 'rep':rep, 'stream':stream,
                           'source_b64':base64.b64encode(source).decode(),
                           'initial':snapshot(work,policy)}
                    raw['cases'].append(row)
                    row['first'] = invocation(work,policy,cut,stream)
                    row['after_first'] = snapshot(work,policy)
                    expected_code = 0 if cut == 'normal' else 73
                    if row['first']['returncode'] != expected_code:
                        raise RuntimeError('STOP_FIRST_PROCESS_EXIT:'+cid)
                    row['recovery'] = invocation(work,policy,'normal',stream)
                    row['final'] = snapshot(work,policy)
                    if row['recovery']['returncode'] != 0:
                        raise RuntimeError('STOP_RECOVERY_PROCESS_EXIT:'+cid)
                    # No scientific decisions in this orchestrator; raw-only auditor decides.
                    durable(root/'raw.json', raw)
    except Exception as e:
        raw['stop'] = {'type':type(e).__name__, 'detail':str(e)}
    raw['finished_ns'] = time.time_ns()
    durable(root/'raw.json',raw)
    print(json.dumps({'rows':len(raw['cases']), 'stop':raw['stop'],
                      'raw_sha256':digest((root/'raw.json').read_bytes())}))
    return 0 if raw['stop'] is None else 2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['worker','construction','formal','freeze'])
    p.add_argument('--out',type=Path)
    p.add_argument('--allocation',default='host-crash-3931-20260922-01')
    p.add_argument('--policy',choices=POLICIES)
    p.add_argument('--cut',choices=CUTS)
    p.add_argument('--stream')
    a = p.parse_args()
    if a.mode == 'freeze':
        verify_reader()
        f = {'allocation':a.allocation, 'source_sha256':source_hashes(), 'environment':environment(),
             'reader_git_blob':READER_BLOB,'base_main':'b2457b746a6df06f6536585dfe2ab937aff639f4',
             'cases':45, 'repetitions':3, 'policies':list(POLICIES), 'cuts':list(CUTS),
             'frozen_ns':time.time_ns(), 'formal_invocations_at_freeze':0}
        with (HERE/'FREEZE.json').open('xb') as out:
            out.write(encode(f))
        print(json.dumps(f,indent=2)); return 0
    if a.out is None:
        p.error('--out is required')
    if a.mode == 'worker':
        if not a.policy or not a.cut or not a.stream:
            p.error('worker requires --policy, --cut and --stream')
        return worker(a.out,a.policy,a.cut,a.stream)
    return run(a.out,a.allocation,a.mode)


if __name__ == '__main__':
    sys.exit(main())
