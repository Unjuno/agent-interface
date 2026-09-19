#!/usr/bin/env python3
"""Local failure-injection experiment. No public network or user data is used."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import random
import sqlite3
import subprocess
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

HERE = Path(__file__).resolve().parent
RUNTIME = HERE / 'source/compiled_gui_interface_v1.py'
RUNTIME_BLOB = '0c02db714127c8e0f770f9d4ac03699749899d2b'
BASE = '29a9c45c87cf59d6d9116b157eed6e737b1311f3'
SCENARIOS = ('stable', 'invalid_before_validation', 'pre_commit_exit',
             'post_commit_exit', 'post_receive_exit')
EXIT_CODE = 73

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)

def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def event(path, kind, **fields):
    row = {'event': kind, 'ns': time.monotonic_ns(), 'pid': os.getpid(), **fields}
    with Path(path).open('a') as f:
        f.write(canonical(row) + '\n'); f.flush(); os.fsync(f.fileno())

def connect(path):
    con = sqlite3.connect(str(path), isolation_level=None, timeout=3)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=FULL')
    return con

def load_runtime():
    data = RUNTIME.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if actual != RUNTIME_BLOB:
        raise RuntimeError('runtime source identity mismatch')
    spec = importlib.util.spec_from_file_location('retained_cgi', RUNTIME)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

def receiver(root, dedup):
    root = Path(root)
    con = connect(root / 'receiver.sqlite')
    con.executescript('''
      CREATE TABLE effects(seq INTEGER PRIMARY KEY, command_id TEXT NOT NULL,
          payload TEXT NOT NULL, committed_ns INTEGER NOT NULL);
      CREATE TABLE requests(seq INTEGER PRIMARY KEY, command_id TEXT NOT NULL,
          payload TEXT NOT NULL, status TEXT NOT NULL, effect_seq INTEGER,
          handled_ns INTEGER NOT NULL);
    ''')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            if self.path != '/effect':
                self.send_error(404); return
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length < 8192:
                self.send_error(400); return
            value = json.loads(self.rfile.read(length))
            if set(value) != {'command_id', 'payload'} or type(value['command_id']) is not str:
                self.send_error(400); return
            key, payload = value['command_id'], canonical(value['payload'])
            con.execute('BEGIN IMMEDIATE')
            try:
                prior = con.execute('SELECT * FROM effects WHERE command_id=? ORDER BY seq LIMIT 1', (key,)).fetchone()
                if dedup and prior is not None:
                    status = 'duplicate' if prior['payload'] == payload else 'conflict'
                    effect_seq = prior['seq']
                else:
                    cur = con.execute('INSERT INTO effects(command_id,payload,committed_ns) VALUES(?,?,?)',
                                      (key, payload, time.monotonic_ns()))
                    effect_seq, status = cur.lastrowid, 'applied'
                con.execute('INSERT INTO requests(command_id,payload,status,effect_seq,handled_ns) VALUES(?,?,?,?,?)',
                            (key, payload, status, effect_seq, time.monotonic_ns()))
                con.execute('COMMIT')
            except BaseException:
                if con.in_transaction: con.execute('ROLLBACK')
                raise
            result = canonical({'status': status, 'effect_seq': effect_seq}).encode()
            self.send_response(409 if status == 'conflict' else 200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(result)))
            self.end_headers(); self.wfile.write(result); self.wfile.flush()
    server = HTTPServer(('127.0.0.1', 0), Handler)
    save(root / 'receiver_ready.json', {'port': server.server_port, 'pid': os.getpid(),
                                      'dedup': bool(dedup)})
    server.serve_forever(poll_interval=.02)

def send(port, key, payload):
    # Explicitly disable proxy discovery; this is a localhost-only fixture.
    opener = build_opener(ProxyHandler({}))
    req = Request(f'http://127.0.0.1:{port}/effect',
                  data=canonical({'command_id': key, 'payload': payload}).encode(),
                  headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with opener.open(req, timeout=4) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 409: return json.load(exc)
        raise

def initialize(case):
    con = connect(case / 'local.sqlite')
    con.executescript('''
      CREATE TABLE state(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
          branch TEXT NOT NULL, guard INTEGER NOT NULL, context TEXT NOT NULL);
      INSERT INTO state VALUES(1,'A',1,'document-A');
      CREATE TABLE commands(command_id TEXT PRIMARY KEY,payload TEXT NOT NULL,
          accepted_ns INTEGER NOT NULL);
      CREATE TABLE outbox(command_id TEXT PRIMARY KEY,payload TEXT NOT NULL,
          delivered INTEGER NOT NULL DEFAULT 0);
      CREATE TABLE acknowledgements(command_id TEXT PRIMARY KEY,status TEXT NOT NULL,
          effect_seq INTEGER NOT NULL);
    ''')
    con.close()

def interface():
    def branch(when, outcome, action=None, next_state=None):
        return dict(when=when, outcome=outcome, action=action, next_state=next_state, reason=None)
    return {'format': 'compiled-gui-interface-v1', 'interface_id': 'external-effect-dev',
        'session_scope': 'local-processes', 'surface': 'cooperative-service',
        'predicates': ['ready', 'local_committed', 'delivered'],
        'symbols': {'destination': {'kind': 'target_reference', 'target_reference': 'local-receiver',
                     'identity_predicate': 'ready', 'dependencies': ['ready']}},
        'actions': {'publish': {'target_symbol': 'destination', 'operation': 'publish',
                   'expected_effect': {'local_committed': True, 'delivered': True}}},
        'method': {'name': 'publish-once', 'version': '1', 'initial_state': 'ready',
                   'max_transitions': 1, 'max_runtime_ms': 10000,
                   'states': {'ready': {'branches': [branch({'ready': True}, 'action', 'publish', 'done')]},
                              'done': {'branches': [branch({'local_committed': True, 'delivered': True}, 'complete')]}}}}

class Adapter:
    def __init__(self, job, case):
        self.job, self.case = job, case
        self.con = connect(case / 'local.sqlite')
        self.seq, self.token = 0, None
        self.log = case / 'initial_events.jsonl'
    def observe(self, request):
        self.seq += 1
        state = dict(self.con.execute('SELECT * FROM state').fetchone())
        committed = self.con.execute('SELECT COUNT(*) FROM commands').fetchone()[0] == 1
        delivered = self.con.execute('SELECT COUNT(*) FROM acknowledgements').fetchone()[0] == 1
        pred = {'ready': state['branch'] == 'A' and state['guard'] == 1 and state['context'] == 'document-A',
                'local_committed': committed, 'delivered': delivered}
        # Canonical state identity does not depend on a requested projection.
        digest = hashlib.sha256(canonical({'state': state, 'predicates': pred}).encode()).hexdigest()
        result = dict(sequence=self.seq, captured_ns=time.perf_counter_ns(), surface='cooperative-service',
                      predicates=pred, evidence_ref=f'obs{self.seq}', evidence_digest=digest)
        event(self.log, 'observation', request=request, state=state, observation=result)
        return result
    def admit(self, request):
        if self.job['scenario'] == 'invalid_before_validation':
            other = connect(self.case / 'local.sqlite')
            other.execute("UPDATE state SET branch='B'"); other.close()
            event(self.log, 'intervention', branch='B')
        self.con.execute('BEGIN IMMEDIATE')
        state = dict(self.con.execute('SELECT * FROM state').fetchone())
        ok = state['branch'] == 'A' and state['guard'] == 1 and state['context'] == 'document-A'
        self.token = 'permit-' + self.job['id'] if ok else None
        event(self.log, 'admission', eligible=ok, source_sequence=request['observation']['sequence'], state=state)
        if not ok: self.con.execute('ROLLBACK')
        return dict(eligible=ok, status='revalidated' if ok else 'denied', authorization=self.token,
                    expected_sequence=self.seq, valid_until_ns=time.perf_counter_ns()+5_000_000_000)
    def crash(self, point):
        event(self.log, 'injected_exit', point=point, exit_code=EXIT_CODE)
        os._exit(EXIT_CODE)
    def deliver(self):
        event(self.log, 'send_started', command_id=self.job['id'])
        result = send(self.job['port'], self.job['id'], self.job['payload'])
        event(self.log, 'receiver_ack_observed', result=result)
        if self.job['scenario'] == 'post_receive_exit':
            self.crash('receiver_committed_before_durable_ack')
        if result['status'] not in ('applied', 'duplicate'): raise RuntimeError(result)
        self.con.execute('INSERT INTO acknowledgements VALUES(?,?,?)',
                         (self.job['id'], result['status'], result['effect_seq']))
        if self.job['arm'] == 'outbox':
            self.con.execute('UPDATE outbox SET delivered=1 WHERE command_id=?', (self.job['id'],))
    def execute(self, request):
        if request['authorization'] != self.token or self.token is None or not self.con.in_transaction:
            raise RuntimeError('invalid one-use authorization')
        self.token = None
        event(self.log, 'execute_started', request=request)
        self.con.execute('INSERT INTO commands VALUES(?,?,?)',
                         (self.job['id'], canonical(self.job['payload']), time.monotonic_ns()))
        if self.job['arm'] == 'inline':
            self.deliver()
        else:
            self.con.execute('INSERT INTO outbox(command_id,payload) VALUES(?,?)',
                             (self.job['id'], canonical(self.job['payload'])))
        if self.job['scenario'] == 'pre_commit_exit': self.crash('before_local_commit')
        self.con.execute('COMMIT')
        event(self.log, 'local_commit_observed')
        if self.job['scenario'] == 'post_commit_exit': self.crash('after_local_commit')
        if self.job['arm'] == 'outbox':
            self.con.execute('BEGIN IMMEDIATE')
            self.deliver()
            self.con.execute('COMMIT')
        event(self.log, 'durable_ack_observed')
        return dict(status='completed', action_id='action1', effect_ref='effect1',
                    release={'verified': True, 'keys_down': [], 'buttons_down': []})
    def close(self):
        if self.con.in_transaction: self.con.execute('ROLLBACK')
        self.con.close(); self.token = None
    def run(self):
        return load_runtime().run(interface(), {'observe': self.observe, 'admit': self.admit,
            'execute': self.execute, 'verify_effect': lambda r: {'status': 'succeeded', 'evidence_ref': r['observation']['evidence_ref']},
            'cancelled': lambda: False, 'journal': lambda row: event(self.log, 'runtime', row=row)})

def worker(case, recover=False):
    case = Path(case); job = json.loads((case / 'job.json').read_text())
    if recover:
        con = connect(case / 'local.sqlite')
        log = case / 'recovery_events.jsonl'
        pending = [dict(r) for r in con.execute('SELECT * FROM outbox WHERE delivered=0')]
        event(log, 'recovery_started', pending=len(pending))
        for row in pending:
            result = send(job['port'], row['command_id'], json.loads(row['payload']))
            event(log, 'receiver_ack_observed', result=result)
            if result['status'] not in ('applied', 'duplicate'): raise RuntimeError(result)
            con.execute('BEGIN IMMEDIATE')
            con.execute('INSERT INTO acknowledgements VALUES(?,?,?)', (row['command_id'], result['status'], result['effect_seq']))
            con.execute('UPDATE outbox SET delivered=1 WHERE command_id=?', (row['command_id'],))
            con.execute('COMMIT')
        event(log, 'recovery_finished', dispatched=len(pending)); con.close()
        save(case / 'recovery_receipt.json', {'pending_before': len(pending), 'dispatched': len(pending)})
        return
    adapter = Adapter(job, case)
    try:
        receipt = adapter.run()
        save(case / 'runtime_receipt.json', receipt)
    finally:
        adapter.close()

def snapshot(case, receiver_db, key):
    con = connect(case / 'local.sqlite')
    local = {t: [dict(r) for r in con.execute('SELECT * FROM '+t)]
             for t in ('state','commands','outbox','acknowledgements')}
    con.close()
    con = connect(receiver_db)
    remote = {t: [dict(r) for r in con.execute('SELECT * FROM '+t+' WHERE command_id=? ORDER BY seq', (key,))]
              for t in ('effects','requests')}
    con.close()
    return {'local': local, 'remote': remote, 'snapshot_ns': time.monotonic_ns()}

def run(out, dedup=False, reps=10):
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=False)
    runtime = load_runtime()
    save(out/'interface.json', interface())
    cpu = [s for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith(('model name', 'cpu MHz'))][:2]
    save(out/'environment.json', {'python': sys.version, 'sqlite': sqlite3.sqlite_version,
        'platform': platform.platform(), 'cpu_info': cpu, 'visible_cpus': os.cpu_count(),
        'batch': 1, 'clock_pinned': False, 'receiver_dedup': dedup, 'base': BASE,
        'runtime_blob': RUNTIME_BLOB, 'transport': 'HTTP/1.0 localhost', 'journal_mode': 'WAL',
        'synchronous': 'FULL', 'injected_process_exit': EXIT_CODE})
    arms = ('outbox',) if dedup else ('inline','outbox')
    schedule = [(arm, scenario, rep) for rep in range(reps) for scenario in SCENARIOS for arm in arms]
    random.Random(22801).shuffle(schedule)
    save(out/'schedule.json', schedule)
    log = (out/'receiver.stderr').open('w')
    proc = subprocess.Popen([sys.executable, __file__, 'receiver', str(out)] + (['--dedup'] if dedup else []),
                            stdout=log, stderr=log)
    try:
        deadline = time.monotonic()+5
        while not (out/'receiver_ready.json').exists():
            if proc.poll() is not None or time.monotonic() > deadline: raise RuntimeError('receiver setup failed')
            time.sleep(.01)
        port = json.loads((out/'receiver_ready.json').read_text())['port']
        for i,(arm,scenario,rep) in enumerate(schedule):
            case = out/f'case-{i:03d}'; case.mkdir()
            key = f'{out.name}-{i:03d}'
            job = {'id': key, 'arm': arm, 'scenario': scenario, 'rep': rep, 'port': port,
                   'payload': {'operation': 'record_effect', 'context': 'document-A', 'value': 1},
                   'receiver_dedup': dedup}
            save(case/'job.json', job); initialize(case)
            save(case/'before.json', snapshot(case, out/'receiver.sqlite', key))
            with (case/'initial.stdout').open('w') as stdout, (case/'initial.stderr').open('w') as stderr:
                initial = subprocess.run([sys.executable, __file__, 'worker', str(case)], stdout=stdout, stderr=stderr, timeout=12)
            save(case/'exit.json', {'initial': initial.returncode})
            expected_exit = 0 if scenario in ('stable','invalid_before_validation') else EXIT_CODE
            if initial.returncode != expected_exit: raise RuntimeError(f'unexpected initial exit: {case} {initial.returncode}')
            save(case/'after_initial.json', snapshot(case, out/'receiver.sqlite', key))
            with (case/'recovery.stdout').open('w') as stdout, (case/'recovery.stderr').open('w') as stderr:
                recovered = subprocess.run([sys.executable, __file__, 'recover', str(case)], stdout=stdout, stderr=stderr, timeout=12)
            save(case/'exit.json', {'initial': initial.returncode, 'recovery': recovered.returncode})
            if recovered.returncode: raise RuntimeError('unexpected recovery exit')
            save(case/'after_recovery.json', snapshot(case, out/'receiver.sqlite', key))
            event(out/'completed.jsonl', 'completed', case=case.name, job=job)
        save(out/'run_status.json', {'status': 'COMPLETED', 'cases': len(schedule)})
    except BaseException:
        save(out/'run_status.json', {'status': 'INCOMPLETE', 'error': traceback.format_exc()})
        raise
    finally:
        proc.terminate(); proc.wait(timeout=5); log.close()
    print(canonical({'out':str(out),'cases':len(schedule),'dedup':dedup}))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['receiver','worker','recover','run'])
    parser.add_argument('path',type=Path)
    parser.add_argument('--dedup',action='store_true')
    parser.add_argument('--reps',type=int,default=10)
    a=parser.parse_args()
    if a.mode=='receiver': receiver(a.path,a.dedup)
    elif a.mode=='worker': worker(a.path)
    elif a.mode=='recover': worker(a.path,True)
    else: run(a.path,a.dedup,a.reps)
if __name__=='__main__': main()
