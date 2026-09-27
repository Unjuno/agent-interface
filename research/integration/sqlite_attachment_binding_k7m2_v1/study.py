"""One-use deterministic subprocess batches; all task effects stay in private DBs."""
import hashlib
import json
import os
from pathlib import Path
import selectors
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
POLICIES = ('SCHEMA_ONLY', 'BINDING_SCOPED')
SCENARIOS = ('STABLE', 'CURRENT_WRITE', 'UNRELATED_WRITE', 'REBIND_PRE',
             'REBIND_PRE_CURRENT_WRITE', 'REBIND_PRE_OLD_WRITE',
             'REBIND_POST', 'OTHER_ALIAS_POST')


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze():
    frozen = json.loads((ROOT / 'FREEZE.json').read_text())
    for name, digest in frozen['sources'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('SOURCE_CHANGED:' + name)


def init_db(root):
    for name, table in [('A', 'alpha'), ('B', 'beta'), ('U', 'alpha')]:
        db = sqlite3.connect(root / (name + '.db'))
        db.executescript('CREATE TABLE alpha(value TEXT,revision INTEGER);'
                        'CREATE TABLE beta(value TEXT,revision INTEGER);'
                        'CREATE VIEW v_dep AS SELECT value,revision FROM ' + table + ';'
                        "INSERT INTO alpha VALUES('a0',1);INSERT INTO beta VALUES('b0',1);")
        db.commit()
        db.close()
    db = sqlite3.connect(root / 'main.db')
    db.execute('CREATE TABLE effects(value TEXT,prepared_binding INTEGER)')
    db.commit()
    db.close()


class Actor:
    def __init__(self, role, root, policy):
        self.role = role
        self.stdin_log = (root / (role + '.stdin')).open('xb')
        self.stdout_log = (root / (role + '.stdout')).open('xb')
        self.stderr_log = (root / (role + '.stderr')).open('xb')
        self.argv = [sys.executable, '-B', str(ROOT / 'actor.py'), role, str(root), policy]
        self.p = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=self.stderr_log, bufsize=0,
                                  env={'PATH': os.defpath, 'PYTHONHASHSEED': '0'})
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.p.stdout, selectors.EVENT_READ)

    def ask(self, req):
        data = (json.dumps(req, sort_keys=True) + '\n').encode()
        self.stdin_log.write(data)
        self.stdin_log.flush()
        self.p.stdin.write(data)
        response = bytearray()
        deadline = time.monotonic() + 3
        while not response.endswith(b'\n'):
            if not self.selector.select(max(0, deadline - time.monotonic())):
                raise TimeoutError(self.role + '_RESPONSE')
            b = os.read(self.p.stdout.fileno(), 1)
            if not b:
                raise EOFError(self.role + '_RESPONSE')
            response.extend(b)
            if len(response) > 262144:
                raise ValueError('OVERSIZED_RESPONSE')
        self.stdout_log.write(response)
        self.stdout_log.flush()
        parsed = json.loads(response)
        if parsed.get('ok') is not True:
            raise ValueError('ACTOR_FAILED')
        return parsed['result']

    def close(self):
        self.p.stdin.close()
        try:
            code = self.p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.p.kill()
            code = self.p.wait()
        self.selector.close()
        self.stdin_log.close()
        self.stdout_log.close()
        self.stderr_log.close()
        return {'argv': self.argv, 'pid': self.p.pid, 'returncode': code}


def case(root, scenario, policy, rep):
    root.mkdir()
    init_db(root)
    actors = {}
    result = {'scenario': scenario, 'policy': policy, 'repetition': rep,
              'calls': [], 'processes': {}, 'error': None}
    def rpc(role, tag, **request):
        start = time.monotonic_ns()
        response = actors[role].ask(request)
        result['calls'].append({'role': role, 'tag': tag, 'request': request,
                                'response': response, 'start_ns': start,
                                'end_ns': time.monotonic_ns()})
        return response
    try:
        actors['reader'] = Actor('reader', root, policy)
        actors['peer'] = Actor('peer', root, policy)
        rpc('peer', 'initial', op='snapshot')
        rpc('reader', 'warm', op='prepare')
        selected = 'A'
        if scenario.startswith('REBIND_PRE'):
            rpc('reader', 'pre_bind', op='bind', alias='slot', database='B')
            selected = 'B'
        rpc('reader', 'prepared', op='prepare')
        rpc('peer', 'at_prepare', op='snapshot')
        table = {'CURRENT_WRITE': 'alpha', 'UNRELATED_WRITE': 'beta',
                 'REBIND_PRE_CURRENT_WRITE': 'beta', 'REBIND_PRE_OLD_WRITE': 'alpha'}.get(scenario)
        if table:
            rpc('peer', 'mutation', op='mutate', database=selected, table=table)
        if scenario in ('REBIND_POST', 'OTHER_ALIAS_POST'):
            rpc('reader', 'post_bind', op='bind', alias='slot' if scenario == 'REBIND_POST' else 'other', database='B')
        rpc('peer', 'at_commit', op='snapshot')
        rpc('reader', 'decision', op='validate')
        rpc('peer', 'final', op='snapshot')
        rpc('reader', 'reader_stop', op='stop')
        rpc('peer', 'peer_stop', op='stop')
    except Exception as exc:
        result['error'] = repr(exc)
    finally:
        for role, actor in actors.items():
            result['processes'][role] = actor.close()
        result['file_hashes'] = {p.name: sha(p) for p in sorted(root.iterdir()) if p.is_file()}
        save(root / 'CASE.json', result)
    if result['error'] or any(p['returncode'] != 0 for p in result['processes'].values()):
        raise RuntimeError('CASE_STOP:' + root.name)


def batch(out, index, construction=False):
    out = Path(out).resolve()
    if not construction:
        verify_freeze()
    out.mkdir(exist_ok=True)
    target = out / ('batch-%d' % index)
    target.mkdir()  # A consumed directory is never reused.
    cases = [(s, p, r) for s in SCENARIOS for r in range(1 if construction else 2) for p in POLICIES]
    chosen = cases if construction else cases[index * 8:(index + 1) * 8]
    if not chosen:
        raise ValueError('EMPTY_BATCH')
    if not construction and index > 0:
        previous = json.loads((out / ('EXIT-%d.json' % (index - 1))).read_text())
        if previous['returncode'] != 0:
            raise ValueError('PREVIOUS_BATCH_NOT_SUCCESSFUL')
    for n, (s, p, r) in enumerate(chosen):
        case(target / ('case-%02d' % n), s, p, r)
    save(target / 'DONE.json', {'count': len(chosen), 'batch': index,
                              'cases': {p.parent.name: sha(p) for p in sorted(target.glob('*/CASE.json'))}})
    print(json.dumps({'batch': index, 'count': len(chosen), 'done_sha256': sha(target / 'DONE.json')}))


if __name__ == '__main__':
    batch(sys.argv[1], int(sys.argv[2]), '--construction' in sys.argv)
