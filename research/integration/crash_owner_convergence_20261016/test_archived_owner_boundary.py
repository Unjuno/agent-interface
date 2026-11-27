"""Offline characterization of archived #8876 codec/client, never its service."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
import types
import unittest

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
sys.path[:0] = [str(ROOT / 'research/doom'), str(ROOT / 'research/live_control')]
from lease_release_v1 import Lease
from test_map01_process_identity_backend import backend_fixture
from executor_v3 import DecisionRequired

ROWS = []

def candidate():
    manifest = json.loads((PACKET / 'ORIGINAL_PATHS.json').read_text())
    row = next(r for r in manifest['entries'] if r['original_path'] ==
               'research/live_control/input_owner_process_v1.py')
    raw = (PACKET / row['archive']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('Archived candidate source hash differs')
    tree = ast.parse(raw)
    names = {'SCHEMA', 'REQUEST_FIELDS', 'LEASE_FIELDS', 'OPERATIONS', 'DOOM_KEYS',
             'RESPONSE_SCHEMA', 'encode_lease', 'decode_lease', 'validate_request'}
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(node)
        elif isinstance(node, ast.ClassDef) and node.name == 'InputOwnerProcess':
            node.body = [m for m in node.body if isinstance(m, ast.FunctionDef) and
                         m.name in {'call', '_sync_records'}]
            selected.append(node)
    module = types.ModuleType('archived_rpc_methods')
    module.__dict__.update(json=json, threading=threading, time=time, Lease=Lease)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(PACKET / row['archive']), 'exec'), module.__dict__)
    return module


def lease():
    value = Lease(time.perf_counter_ns() + 10_000_000_000)
    value.intent_token = 'offline-owned-intent'
    value.expected_focus = value.expected_surface = 41
    value.expected_geometry = [0, 0, 32, 32]
    return value


class ArchivedOwnerBoundaryTests(unittest.TestCase):
    def test_wire_drops_current_process_and_window_source_identity(self):
        c = candidate()
        original = lease()
        original.target_process_identity = (7, 41, 'a' * 64, original.deadline)
        original.target_window_identity = (7, 41, 'b' * 64, original.deadline)
        sources_before = {name: list(getattr(original, name)) for name in ('target_process_identity', 'target_window_identity')}
        wire = c.encode_lease(original)
        decoded = c.decode_lease(json.loads(json.dumps(wire)), {})
        self.assertFalse(hasattr(decoded, 'target_process_identity'))
        self.assertFalse(hasattr(decoded, 'target_window_identity'))
        original.target_process_identity = (7, 41, 'c' * 64, original.deadline)
        original.target_window_identity = (7, 41, 'd' * 64, original.deadline)
        self.assertEqual(c.encode_lease(original), wire)
        ROWS.append(dict(case='generation_wire_collision', classification='FAIL_CURRENT_IDENTITY_TRANSFER',
                         wire=wire, dropped_fields=['target_process_identity', 'target_window_identity'],
                         changed_source_same_wire=True, sources_before=sources_before,
                         sources_after={name: list(getattr(original, name)) for name in sources_before},
                         wire_after=c.encode_lease(original)))

    def test_selected_current_owner_refuses_decoded_lease(self):
        c = candidate()
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('offline-source', 0)
            original = lease()
            backend.bind_lease_source(original, backend.sequence)
            decoded = c.decode_lease(c.encode_lease(original), {})
            with self.assertRaises(DecisionRequired):
                backend.owner.call('down', decoded, 'a')
            self.assertEqual(fake.down, set())
            self.assertFalse(any(r.get('event') == 'input_admission' for r in backend.owner.records))
            ROWS.append(dict(case='selected_owner_decoded_lease', classification='PASS_FAIL_CLOSED_CONTROL',
                             admitted=0, fake_keys_down=[], owner_records=backend.owner.records))
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('offline-source-control', 0)
            original = lease()
            backend.bind_lease_source(original, backend.sequence)
            admission = backend.owner.call('down', original, 'a')
            self.assertEqual(fake.down, {38})
            backend.owner.call('release', original)
            self.assertEqual(fake.down, set())
            ROWS.append(dict(case='selected_owner_original_lease', classification='PASS_FAKE_X_CONTROL',
                             admitted=1, admission=admission, fake_keys_down_after_release=[], owner_records=backend.owner.records))

    def test_unknown_or_invalid_reply_does_not_quarantine_next_send(self):
        for failure in ('timeout', 'wrong_reply_id', 'invalid_records', 'healthy_control'):
            with self.subTest(failure=failure):
                c = candidate()
                owner = c.InputOwnerProcess.__new__(c.InputOwnerProcess)
                owner._closed = False
                owner._rpc_lock = threading.Lock()
                owner._leases_lock = threading.Lock()
                owner._records_lock = threading.Lock()
                owner._leases = {}; owner._lease_cancel_threads = {}
                owner._records = []; owner._records_version = 0
                owner._next_request_id = 1
                owner._rpc = object(); owner._rpc_buffer = bytearray(); owner.rpc_timeout = .1
                sent = []
                c._send_frame = lambda _sock, request: sent.append(json.loads(json.dumps(request)))
                def receive(_sock, _buffer, _timeout):
                    response = dict(schema=c.RESPONSE_SCHEMA, request_id=sent[-1]['request_id'],
                                    ok=True, result='synthetic_ack', records_version=0, records=[])
                    if len(sent) == 1:
                        if failure == 'timeout': raise TimeoutError('injected no reply')
                        if failure == 'wrong_reply_id': response['request_id'] = 999
                        if failure == 'invalid_records': response['records'] = None
                    return response
                c._receive_frame = receive
                active = lease()
                error = None
                try: owner.call('down', active, 'a')
                except (RuntimeError, ValueError) as exc: error = str(exc)
                self.assertEqual(error is None, failure == 'healthy_control')
                owner.call('down', active, 'd')
                self.assertEqual([r['request_id'] for r in sent], [1, 2])
                self.assertEqual([r['key'] for r in sent], ['a', 'd'])
                ROWS.append(dict(case=failure, classification='PASS_SYNTHETIC_CONTROL' if error is None else
                                 'FAIL_NO_STICKY_RPC_QUARANTINE', first_error=error, sent=sent,
                                 scope='Intercepted sends only; no service, socket or native input'))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ArchivedOwnerBoundaryTests))
    source_pins = {}
    for loaded in list(sys.modules.values()):
        filename = getattr(loaded, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                source_pins[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    source_pins[Path(__file__).resolve().relative_to(ROOT).as_posix()] = hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    args.out.write_text(json.dumps(dict(rows=ROWS, source_sha256_lf=source_pins, tests=result.testsRun, failures=len(result.failures),
                                       errors=len(result.errors), skipped=len(result.skipped)), indent=2) + '\n', encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
