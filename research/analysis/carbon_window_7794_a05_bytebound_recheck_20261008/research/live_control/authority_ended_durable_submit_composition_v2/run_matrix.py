from __future__ import annotations
import hashlib, json, os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent
DUR = LIVE / 'authority_ended_restart_durability_v1'
FIXTURE = LIVE / 'authority_ended_receipt_ledger_v1' / 'receipt-fixture.json'
# Durable token's bridge must resolve from its retained directory.
sys.path.insert(0, str(LIVE))
sys.path.insert(0, str(DUR))
from durable_token_state_v2 import DurableTokenLedger, TokenConsumed
from durable_submit_v1 import initialize as submit_initialize, run as submit_run
from received_continuation_v1 import start as continuation_start

EXPECTED_BLOBS = {
    DUR / 'durable_token_state_v2.py': 'e48f4e2c1949ffd494a7e4e61510e9d3148aa646',
    DUR / 'authority_ended_bridge_v1.py': '9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1',
    LIVE / 'durable_submit_v1.py': 'aaee9d460bcf114dbe1603056c79e6ecc65403e2',
    LIVE / 'received_continuation_v1.py': 'b27d922799cfcfc66ad092c8edb8b7134e1889e5',
    LIVE / 'unix_json_deadline.py': '267b5ccce24ca43b8a6e9b36219d50342888aa27',
    FIXTURE: '4070fd206c859357125a2cb327affa5aec6de8b8',
}
COMMAND = {'op': 'submit', 'expected_sequence': 3, 'valid_until_ns': 9_999_999_999_999,
           'steps': [{'op': 'observe'}]}

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def assert_sources():
    got = {}
    for path, expected in EXPECTED_BLOBS.items():
        actual = git_blob_sha(path)
        if actual != expected:
            raise AssertionError(f'blob mismatch {path}: {actual} != {expected}')
        got[str(path.relative_to(LIVE))] = {'git_blob_sha1': actual, 'sha256': sha256(path)}
    return got

def load_json(path: Path):
    return json.loads(path.read_text())

def token_status(path: Path, rid: str):
    return load_json(path)['entries'][rid]['status']

def classify(token_path: Path, submit_path: Path, rid: str):
    t = token_status(token_path, rid)
    s = load_json(submit_path)
    pending = s['pending']
    if t == 'pending' and pending is None:
        return 'TOKEN_PENDING_NO_SUBMIT'
    if t == 'consumed' and pending is None:
        return 'CONSUMED_WITHOUT_SUBMIT_RECORD'
    if t == 'consumed' and pending is not None:
        return 'PENDING_OR_UNKNOWN_DELIVERY'
    if t == 'pending' and pending is not None:
        return 'SUBMIT_PENDING_BEFORE_TOKEN_CONSUME'
    return 'UNCLASSIFIED'

def setup(root: Path, suffix: str):
    root.mkdir(parents=True, exist_ok=False)
    token_path = root / 'token-state.json'
    submit_path = root / 'submit-journal.json'
    receipt = load_json(FIXTURE)
    ledger = DurableTokenLedger(token_path, initialize=True)
    token = ledger.issue(receipt)
    submit_initialize(submit_path, continuation_start('compose-fixture-' + suffix))
    return token_path, submit_path, token.authority_end_id

def worker(mode: str, root: Path):
    token_path = root / 'token-state.json'
    submit_path = root / 'submit-journal.json'
    rid = load_json(FIXTURE)['authority_end_id']
    if mode == 'consume_crash':
        ledger = DurableTokenLedger(token_path)
        token = ledger.recover_pending(rid)
        ledger.consume(token)
        os._exit(81)
    if mode == 'transport_crash':
        ledger = DurableTokenLedger(token_path)
        token = ledger.recover_pending(rid)
        ledger.consume(token)
        def crash_transport(session, request, **kwargs):
            os._exit(82)
        submit_run(submit_path, {'command': COMMAND, 'timeout': 0}, crash_transport)
        raise AssertionError('transport crash returned')
    if mode == 'blocked_new_command':
        marker = root / 'blocked-transport-reached.json'
        def should_not_run(session, request, **kwargs):
            marker.write_text(json.dumps({'unexpected': True}) + '\n')
            return {'status': 'timeout', 'cursor': 0, 'records': []}
        try:
            submit_run(submit_path, {'command': COMMAND, 'timeout': 0}, should_not_run)
        except ValueError as e:
            (root / 'blocked-result.json').write_text(json.dumps({'error': str(e), 'transport_reached': marker.exists()}, sort_keys=True) + '\n')
            return
        raise AssertionError('new command was not refused')
    if mode == 'read_only_timeout':
        calls = root / 'read-only-calls.json'
        def timeout_read(session, request, **kwargs):
            calls.write_text(json.dumps({'request': request}, sort_keys=True) + '\n')
            if 'command' in request:
                raise AssertionError('read-only recovery attempted command')
            return {'status': 'timeout', 'cursor': 0, 'records': []}
        result = submit_run(submit_path, {'events': ['terminal'], 'timeout': 0}, timeout_read)
        (root / 'read-only-result.json').write_text(json.dumps(result, sort_keys=True) + '\n')
        return
    if mode == 'reverse_transport_crash':
        marker = root / 'reverse-transport.json'
        def crash_transport(session, request, **kwargs):
            marker.write_text(json.dumps({'token_status_at_transport': token_status(token_path, rid), 'request_has_command': 'command' in request}, sort_keys=True) + '\n')
            os._exit(83)
        submit_run(submit_path, {'command': COMMAND, 'timeout': 0}, crash_transport)
        raise AssertionError('reverse transport crash returned')
    raise ValueError(mode)

def child(mode: str, root: Path, expected: int = 0):
    p = subprocess.run([sys.executable, __file__, 'worker', mode, str(root)], capture_output=True, text=True, timeout=15)
    if p.returncode != expected:
        raise AssertionError({'mode': mode, 'expected': expected, 'actual': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    return {'mode': mode, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

def main():
    sources = assert_sources()
    rows = []
    def add(case, passed, detail):
        rows.append({'case': case, 'pass': bool(passed), 'detail': detail})
    with tempfile.TemporaryDirectory(prefix='authority-durable-submit-compose-v1-') as td:
        base = Path(td)
        # A: known-good precondition.
        a = base / 'a-pending'
        ta, sa, rid = setup(a, 'a')
        ca = classify(ta, sa, rid)
        add('pending_token_without_submit_is_recoverable_precondition', ca == 'TOKEN_PENDING_NO_SUBMIT', {'classification': ca})

        # B: exact inter-journal cut after durable consume, before durable_submit.run.
        b = base / 'b-between-journals'
        tb, sb, rid = setup(b, 'b')
        proc_b = child('consume_crash', b, 81)
        cb = classify(tb, sb, rid)
        try:
            DurableTokenLedger(tb).recover_pending(rid)
            recover = 'UNEXPECTED_RECOVERY'
        except TokenConsumed as e:
            recover = str(e)
        add('consume_before_submit_crash_leaves_no_submit_identity',
            cb == 'CONSUMED_WITHOUT_SUBMIT_RECORD' and load_json(sb)['pending'] is None and recover == 'authority_end_id already consumed',
            {'classification': cb, 'token_recovery': recover, 'process': proc_b})

        # C: once durable_submit has committed pending, a crash inside transport retains uncertainty.
        c = base / 'c-after-submit-persist'
        tc, sc, rid = setup(c, 'c')
        proc_c = child('transport_crash', c, 82)
        cc = classify(tc, sc, rid)
        pending_c = load_json(sc)['pending']
        add('transport_crash_after_submit_persist_is_explicit_unknown',
            cc == 'PENDING_OR_UNKNOWN_DELIVERY' and pending_c is not None and pending_c.get('write_state') == 'may_have_been_sent',
            {'classification': cc, 'write_state': pending_c.get('write_state') if pending_c else None, 'process': proc_c})

        # D1: restart refuses blind new command before transport.
        proc_block = child('blocked_new_command', c, 0)
        blocked = load_json(c / 'blocked-result.json')
        add('restart_refuses_blind_new_command_before_transport',
            blocked == {'error': 'unresolved command; read only', 'transport_reached': False},
            {'result': blocked, 'process': proc_block})

        # D2: read-only timeout keeps the same pending identity unresolved.
        before = load_json(sc)['pending']['request']['request_id']
        proc_read = child('read_only_timeout', c, 0)
        after_state = load_json(sc)
        after = after_state['pending']['request']['request_id'] if after_state['pending'] else None
        ro = load_json(c / 'read-only-result.json')
        add('read_only_timeout_preserves_pending_identity_without_command',
            before == after and after_state['pending']['write_state'] == 'may_have_been_sent' and 'command' not in ro['request'],
            {'request_id_before': before, 'request_id_after': after, 'request': ro['request'], 'process': proc_read})

        # E: reversing order is not a token gate: transport is entered while token remains pending.
        e = base / 'e-reverse-order'
        te, se, rid = setup(e, 'e')
        proc_e = child('reverse_transport_crash', e, 83)
        marker = load_json(e / 'reverse-transport.json')
        ce = classify(te, se, rid)
        add('submit_before_consume_reaches_transport_with_token_still_pending',
            marker == {'request_has_command': True, 'token_status_at_transport': 'pending'} and ce == 'SUBMIT_PENDING_BEFORE_TOKEN_CONSUME',
            {'transport_marker': marker, 'classification': ce, 'process': proc_e})

        result = {
            'schema': 'authority-ended-durable-submit-composition-v1-result',
            'base_commit': 'd21482d1a3cc16b54447d14d0a2d93aa70409162',
            'rows': rows,
            'hard_gate_pass': len(rows) == 6 and all(r['pass'] for r in rows),
            'decision': 'RETAIN_COMPOSITION_BOUNDARY_HOLD_ATOMIC_EXACTLY_ONCE' if len(rows) == 6 and all(r['pass'] for r in rows) else 'RETAIN_FAILURE',
            'source_identities': sources,
            'prereg_sha256': sha256(HERE / 'prereg.json'),
            'runner_sha256': None,
            'environment': {
                'python': sys.version.split()[0],
                'platform': platform.platform(),
                'machine': platform.machine(),
                'cpu_count': os.cpu_count(),
            },
            'limits': ['injected transport only', 'single writer', 'process crash only', 'no power-loss claim', 'no live GUI/OS input/network/model'],
        }
        # runner identity is computed after source freeze; this field is filled by publication wrapper.
        print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'worker':
        worker(sys.argv[2], Path(sys.argv[3]))
    else:
        main()
