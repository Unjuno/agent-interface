#!/usr/bin/env python3
"""Issue #197: run the byte-exact runtime; adapters own SQLite effects.
No model, GUI, input backend or wall-time performance inference.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, itertools, json, platform, sqlite3, sys
from pathlib import Path

BLOB = '0c02db714127c8e0f770f9d4ac03699749899d2b'
BASE = '4e8e197115969df81a946176e08362c130136603'
MODES = ('union', 'naive', 'unique', 'certified')

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()

def load_runtime(path):
    data = path.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if actual != BLOB:
        raise ValueError(f'exact runtime required: {actual}')
    spec = importlib.util.spec_from_file_location('frozen_runtime', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def branch(when, outcome='action', action=None, next_state=None, reason=None):
    return dict(when=when, outcome=outcome, action=action, next_state=next_state, reason=reason)

def interface(kind):
    whens = ({'surface_present': True, 'zone': 'LEFT'},
             {'surface_present': True, 'zone': 'RIGHT'}) if kind == 'cert' else (
             {'surface_present': True, 'a': 0},
             {'surface_present': True, 'b': 1, 'c': 1})
    branches = [branch(w, action=f'act_{n}', next_state='done') for n, w in zip('AB', whens)]
    branches.append(branch({'surface_present': False}, 'yield', reason='association_changed'))
    if kind == 'cert':
        branches.append(branch({'surface_present': True, 'zone': 'GOAL'}, 'complete'))
    return {'format': 'compiled-gui-interface-v1', 'interface_id': 'er197-' + kind,
        'session_scope': 'er197-v1', 'surface': 'fixture',
        'predicates': ['surface_present', 'done'] + (['zone'] if kind == 'cert' else ['a', 'b', 'c']),
        'symbols': {'surface': {'kind': 'target_reference', 'target_reference': 'fixture-object',
            'identity_predicate': 'surface_present', 'dependencies': ['surface_present']}},
        'actions': {f'act_{n}': {'target_symbol': 'surface', 'operation': f'apply_{n}',
            'expected_effect': {'done': True}} for n in 'AB'},
        'method': {'name': 'choose_then_apply', 'version': '1', 'initial_state': 'choose',
            'max_transitions': 1, 'max_runtime_ms': 10000,
            'states': {'choose': {'branches': branches}, 'done': {'branches': [
                branch({'done': True}, 'complete')]}}}}

def certificate(branches):
    pairs = []
    for i, j in itertools.combinations(range(len(branches)), 2):
        a, b = branches[i]['when'], branches[j]['when']
        # Match actual runtime Python equality, not type-strict JSON equality.
        witnesses = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
        pairs.append({'pair': [i, j], 'witnesses': witnesses})
    return {'exclusive': all(p['witnesses'] for p in pairs), 'pairs': pairs}

def initial(x=-1):
    return dict(x=x, a=0, b=0, c=0, present=True, binding=1,
                gA=True, gB=True, noise=False, done=False, version=0)

def cases():
    result = []
    for old, now, present, ga, gb, noise in itertools.product(
            (-1, 1), (-1, 0, 1), (False, True), (False, True), (False, True), (False, True)):
        src = initial(old); cur = dict(src, x=now, present=present, gA=ga, gB=gb, noise=noise, version=1)
        result.append(dict(suite='cert_grid', kind='cert', name='grid', source=src, current=cur))
    for old in (-1, 1):
        for name in ('selected_unknown', 'same_branch_motion', 'binding_changed', 'control_unknown'):
            src = initial(old); cur = dict(src, version=1)
            if name == 'selected_unknown': cur['gA' if old < 0 else 'gB'] = None
            elif name == 'same_branch_motion': cur['x'] = old * 7
            elif name == 'binding_changed': cur['binding'] = 2
            else: cur['x'] = None
            result.append(dict(suite='cert_named', kind='cert', name=name, source=src, current=cur))
    for a, b, c, present, ga, gb in itertools.product((0, 1), (0, 1), (0, 1),
                                                    (False, True), (False, True), (False, True)):
        src = initial(); cur = dict(src, a=a, b=b, c=c, present=present, gA=ga, gB=gb, version=1)
        result.append(dict(suite='overlap', kind='overlap', name='grid', source=src, current=cur))
    return result

class Adapter:
    def __init__(self, spec, case, mode):
        self.spec, self.case, self.mode = spec, case, mode
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.execute('CREATE TABLE state(k TEXT PRIMARY KEY, v TEXT NOT NULL)')
        self.db.execute('CREATE TABLE effects(action TEXT NOT NULL, pre_world TEXT NOT NULL)')
        self.store(case['source'])
        self.seq = 0; self.tick = 1_000_000_000
        self.events = []; self.observations = []; self.reads = []
        self.auth = None; self.admission = None; self.execute_calls = 0
        self.cert = certificate(spec['method']['states']['choose']['branches'])

    def clock(self):
        self.tick += 1000
        return self.tick

    def store(self, state):
        self.db.executemany('INSERT OR REPLACE INTO state VALUES (?,?)',
                            [(k, encode(v)) for k, v in state.items()])

    def snapshot(self):
        return {k: json.loads(v) for k, v in self.db.execute('SELECT k,v FROM state ORDER BY k')}

    def read(self, key):
        self.reads.append(key)
        row = self.db.execute('SELECT v FROM state WHERE k=?', (key,)).fetchone()
        return None if row is None else json.loads(row[0])

    @staticmethod
    def predicates(world, kind):
        common = {'surface_present': world['present'], 'done': world['done']}
        if kind == 'cert':
            x = world['x']
            common['zone'] = 'unknown' if x is None else ('LEFT' if x < 0 else 'RIGHT' if x > 0 else 'GOAL')
        else: common.update({k: world[k] for k in ('a', 'b', 'c')})
        return common

    def observe(self, request):
        self.seq += 1; world = self.snapshot()
        obs = dict(sequence=self.seq, captured_ns=self.clock(), surface='fixture',
                   predicates=self.predicates(world, self.case['kind']),
                   evidence_ref=f'obs-{self.seq}', evidence_digest=digest(world))
        self.observations.append({'request': request, 'raw_world': world, 'normalized': copy.deepcopy(obs)})
        return obs

    def admit(self, request):
        # Intervene only after the unmodified runtime has selected an action.
        self.store(self.case['current'])
        self.db.execute('BEGIN IMMEDIATE')
        branches = self.spec['method']['states']['choose']['branches']
        chosen = next(i for i, b in enumerate(branches) if b['action'] == request['action'])
        cache = {}
        def pred(k):
            if k not in cache:
                if k == 'surface_present': cache[k] = self.read('present')
                elif k == 'zone':
                    x = self.read('x')
                    cache[k] = 'unknown' if x is None else ('LEFT' if x < 0 else 'RIGHT' if x > 0 else 'GOAL')
                else: cache[k] = self.read(k)
            return cache[k]
        def match(b): return all(pred(k) == v for k, v in b['when'].items())
        structural = self.read('binding') == self.case['source']['binding'] and pred('surface_present') is True
        selected_guard = 'gA' if chosen == 0 else 'gB'
        guard_ok = self.read(selected_guard) is True
        strategy = self.mode
        if self.mode == 'naive': control = True
        elif self.mode == 'unchecked_selected' or (self.mode == 'certified' and self.cert['exclusive']):
            control = match(branches[chosen]); strategy = 'selected_when'
        else:
            control = [i for i, b in enumerate(branches) if match(b)] == [chosen]
            strategy = 'full_unique'
        other_ok = self.read('gB' if chosen == 0 else 'gA') is True if self.mode == 'union' else True
        ok = bool(structural and guard_ok and control and other_ok)
        final = self.snapshot()  # Retention only; not used to decide eligibility.
        auth_data = dict(action=request['action'], operation=request['operation'],
            source_sequence=request['observation']['sequence'],
            source_digest=request['observation']['evidence_digest'], final_version=final['version'],
            final_digest=digest(final), valid_until_ns=self.clock() + 1_000_000_000, used=False)
        token = digest(auth_data)
        self.admission = dict(eligible=ok, structural=structural, guard=guard_ok, control=control,
            other_guard=other_ok, strategy=strategy, final_world=final, reads=list(self.reads),
            transaction_open=self.db.in_transaction, selected=chosen, token=token if ok else None)
        if ok: self.auth = dict(auth_data, token=token)
        else: self.db.execute('ROLLBACK')
        return dict(eligible=ok, status='revalidated' if ok else ('stale' if structural else 'association_changed'),
            authorization=token if ok else None, expected_sequence=request['observation']['sequence'],
            valid_until_ns=auth_data['valid_until_ns'] if ok else 0)

    def execute(self, request):
        self.execute_calls += 1
        a = self.auth
        if not a or a['used'] or request['authorization'] != a['token'] or not self.db.in_transaction:
            raise ValueError('missing, spent or unprotected authority')
        if (request['action'] != a['action'] or request['operation'] != a['operation'] or
            request['expected_sequence'] != a['source_sequence'] or
            request['valid_until_ns'] != a['valid_until_ns'] or self.clock() >= a['valid_until_ns']):
            raise ValueError('authority binding/expiry mismatch')
        world = self.snapshot()
        if digest(world) != a['final_digest']:
            raise ValueError('final boundary lost coherence')
        a['used'] = True
        self.db.execute('INSERT INTO effects VALUES (?,?)', (request['action'], encode(world)))
        self.store(dict(world, done=True, version=world['version'] + 1))
        self.db.execute('COMMIT')
        return dict(status='completed', action_id='action-1', effect_ref='effect-1',
                    release=dict(verified=True, keys_down=[], buttons_down=[]))

    def verify(self, request):
        effects = self.db.execute('SELECT action FROM effects').fetchall()
        ok = effects == [(request['action'],)] and request['observation']['predicates'].get('done') is True
        return dict(status='succeeded' if ok else 'failed', evidence_ref=request['observation']['evidence_ref'])

    def run(self, runtime):
        try:
            receipt = runtime.run(self.spec, dict(observe=self.observe, admit=self.admit,
                execute=self.execute, verify_effect=self.verify, cancelled=lambda: False,
                journal=lambda e: self.events.append(copy.deepcopy(e))), clock=self.clock)
            effects = [dict(action=a, pre_world=json.loads(w)) for a, w in self.db.execute('SELECT * FROM effects')]
            return dict(case=self.case, mode=self.mode, certificate=self.cert,
                observations=self.observations, admission=self.admission, authority=self.auth,
                execute_calls=self.execute_calls, effects=effects, events=self.events, receipt=receipt,
                transaction_left_open=self.db.in_transaction)
        finally:
            if self.db.in_transaction: self.db.rollback()
            self.db.close()

def main():
    p = argparse.ArgumentParser(); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--runtime', type=Path, default=Path(__file__).parent / 'vendor/compiled_gui_interface_v1.py')
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runtime = load_runtime(args.runtime)
    specs = {kind: interface(kind) for kind in ('cert', 'overlap')}
    for spec in specs.values(): runtime.validate(spec)
    (args.out/'specifications.json').write_text(json.dumps(specs, indent=2)+'\n')
    env = dict(python=sys.version, platform=platform.platform(), sqlite=sqlite3.sqlite_version,
               timer='injected deterministic virtual nanoseconds; not latency data', base=BASE,
               runtime_blob=BLOB, runtime_sha256=hashlib.sha256(args.runtime.read_bytes()).hexdigest(),
               release='simulated adapter contract only; no physical input was issued')
    (args.out/'environment.json').write_text(json.dumps(env, indent=2)+'\n')
    count = 0
    with (args.out/'raw.jsonl').open('x') as out:
        for index, case in enumerate(cases()):
            modes = MODES + (('unchecked_selected',) if case['kind'] == 'overlap' else ())
            for mode in modes:
                try:
                    row = Adapter(specs[case['kind']], case, mode).run(runtime)
                    row['id'] = f'{index:03d}-{mode}'
                    out.write(encode(row)+'\n'); out.flush(); count += 1
                except Exception as exc:
                    (args.out/'failure.json').write_text(encode(dict(index=index,mode=mode,error=repr(exc)))+'\n')
                    raise
    assert count == 736, count
    print(json.dumps({'runtime_invocations': count, 'raw_sha256': hashlib.sha256((args.out/'raw.jsonl').read_bytes()).hexdigest()}))

if __name__ == '__main__': main()
