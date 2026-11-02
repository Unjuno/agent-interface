import time
import tempfile
import unittest
from unittest.mock import Mock

from runtime.backends.win32_v1.backend import (
    Win32Backend, Win32BackendError, Win32ExecutionError,
)
from runtime.core_v1.compiled_gui import run
from runtime.guarded_win32_v1.bridge import MoveBridge
from runtime.guarded_win32_v1.fresh import FreshWin32Reference


def interface():
    return {
        'format': 'compiled-gui-interface-v1',
        'interface_id': 'win32-generation-composition',
        'session_scope': 'fixture-session',
        'surface': 'win32-fixture',
        'predicates': ['ready'],
        'symbols': {'target': {
            'kind': 'target_reference', 'target_reference': 'button',
            'identity_predicate': 'ready', 'dependencies': ['ready']}},
        'actions': {'move': {
            'target_symbol': 'target', 'operation': 'pointer_move',
            'expected_effect': {'ready': True}}},
        'method': {
            'name': 'single-move', 'version': '1', 'initial_state': 'start',
            'max_transitions': 1, 'max_runtime_ms': 5000,
            'states': {
                'start': {'branches': [{
                    'when': {'ready': True}, 'outcome': 'action',
                    'action': 'move', 'next_state': 'done', 'reason': None}]},
                'done': {'branches': [{
                    'when': {'ready': True}, 'outcome': 'complete',
                    'action': None, 'next_state': None, 'reason': None}]},
            },
        },
    }


class CompiledCoreCompositionTests(unittest.TestCase):
    def setup_bridge(self):
        backend = object.__new__(Win32Backend)
        backend.targets = {'fixture': 42}
        backend.emissions = 0
        backend.held_keys = {}
        backend.held_buttons = set()
        backend.user32 = Mock()
        backend.user32.IsWindow.return_value = True
        backend.user32.GetForegroundWindow.return_value = 42
        backend.process_identity = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 700})
        backend.geometry = Mock(return_value={
            'x': 0, 'y': 0, 'width': 8, 'height': 8})
        raw = bytes(v for y in range(8) for x in range(8)
                    for v in (x * 20, y * 20, 255, 0))
        backend._capture_hdc = Mock(return_value=raw)
        events = []
        backend.pointer_move = lambda target, frame, x, y: events.append(
            ['move', target, x, y])

        def release():
            events.append(['release'])
            return {'verified': True, 'keys_down': [], 'buttons_down': [], 'keys_unknown': [], 'buttons_unknown': []}

        backend.release_all = release
        self.image_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.image_dir.cleanup)
        observer = FreshWin32Reference(backend, 'fixture', self.image_dir.name)
        observer.observe([0, 0, 8, 8])
        observer.mint('button', 1, [2, 2, 4, 4])
        bridge = MoveBridge(observer,
            lambda intent: {'lease_id': 'compiled-core-lease',
                'expires_at_ns': time.monotonic_ns() + 4_000_000_000},
            lambda: False)
        return backend, observer, bridge, events

    def execute_compiled(self, *, change_generation_before_execute=False,
                         report_uncertain_execution=False):
        backend, observer, bridge, events = self.setup_bridge()
        call_rows = []
        effect_checks = []

        def observe(_request):
            if not call_rows:
                row, _ = observer.get(1)
            else:
                row = observer.observe([0, 0, 8, 8])
            call_rows.append(row['sequence'])
            return {
                'sequence': row['sequence'],
                'captured_ns': row['capture_ns'],
                'surface': 'win32-fixture',
                'predicates': {'ready': True},
                'evidence_ref': 'frame-' + str(row['sequence']),
                'evidence_digest': 'digest-' + str(row['sequence']),
            }

        def admit(request):
            permit = bridge.prepare_observed('button', [1, 1],
                source_sequence=request['observation']['sequence'])
            return {'eligible': True, 'status': 'revalidated',
                'authorization': permit['authorization'],
                'expected_sequence': permit['sequence'],
                'valid_until_ns': permit['valid_until_ns']}

        def execute(request):
            if change_generation_before_execute:
                backend.process_identity.return_value = {
                    'pid': 52, 'creation_time_100ns': 900}
            result = bridge.execute(request['authorization'])
            if result['status'] != 'completed':
                return {'status': 'refused', 'action_id': 'move-1',
                    'effect_ref': 'effect-1', 'input_dispatched': False,
                    'release': {'verified': False, 'keys_down': [],
                                'buttons_down': []}}
            release = result['execution']['releases'][-1]
            if report_uncertain_execution:
                # The native operation did run and released all input, but the
                # caller cannot certify a complete task effect. Preserve that
                # uncertainty instead of promoting it to a completed action.
                return {'status': 'delivery_uncertain', 'action_id': 'move-1',
                    'effect_ref': 'effect-1', 'input_dispatched': True,
                    'release': {'verified': release['verified'],
                        'keys_down': release['keys_down'],
                        'buttons_down': release['buttons_down']}}
            return {'status': 'completed', 'action_id': 'move-1',
                'effect_ref': 'effect-1', 'input_dispatched': True,
                'release': {'verified': release['verified'],
                    'keys_down': release['keys_down'],
                    'buttons_down': release['buttons_down']}}

        receipt = run(interface(), {
            'observe': observe,
            'admit': admit,
            'execute': execute,
            'verify_effect': lambda request: effect_checks.append(request) or {
                'status': 'succeeded',
                'evidence_ref': request['observation']['evidence_ref']},
            'cancelled': lambda: False,
        }, clock=time.monotonic_ns)
        return receipt, events, call_rows, observer, effect_checks

    def test_compiled_core_executes_against_the_same_observation_generation(self):
        receipt, events, sequences, _, effect_checks = self.execute_compiled()
        self.assertEqual(receipt['outcome'], 'TASK_SUCCEEDED')
        self.assertEqual(receipt['completed_transitions'], 1)
        self.assertEqual(sequences, [1, 2])
        self.assertEqual(events, [['move', 'fixture', 3, 3], ['release']])
        self.assertEqual(len(effect_checks), 1)

    def test_generation_change_after_admission_is_refused_by_live_bridge_guard(self):
        receipt, events, sequences, observer, effect_checks = self.execute_compiled(
            change_generation_before_execute=True)
        self.assertEqual((receipt['outcome'], receipt['reason']),
                         ('SAFE_YIELD', 'execution_refused'))
        self.assertEqual(receipt['completed_transitions'], 0)
        self.assertEqual(sequences, [1])
        self.assertEqual(events, [])
        terminal = next(row for row in receipt['critical_events']
                        if row['event'] == 'action_terminal')
        self.assertFalse(terminal['release_verified'])
        self.assertTrue(observer.review_required)
        self.assertEqual(effect_checks, [])

    def test_uncertain_dispatch_with_verified_release_stops_before_effect_or_replay(self):
        receipt, events, sequences, _, effect_checks = self.execute_compiled(
            report_uncertain_execution=True)
        self.assertEqual((receipt['outcome'], receipt['reason']),
                         ('SAFE_YIELD', 'delivery_uncertain'))
        self.assertEqual(receipt['completed_transitions'], 0)
        self.assertEqual(sequences, [1])
        self.assertEqual(events, [['move', 'fixture', 3, 3], ['release']])
        self.assertEqual(effect_checks, [])
        terminal = next(row for row in receipt['critical_events']
                        if row['event'] == 'action_terminal')
        self.assertTrue(terminal['input_dispatched'])
        self.assertTrue(terminal['release_verified'])

    def test_partial_multichar_text_delivery_releases_and_never_replays(self):
        backend, observer, _, _ = self.setup_bridge()
        backend.pending_unicode_ups = set()
        backend.preflight = lambda _program: None
        backend.release_all = Win32Backend.release_all.__get__(backend)
        sends = []
        fail_once = {'enabled': True}

        def send_unicode_unit(unit, down):
            sends.append((unit, down))
            if unit == ord('B') and down is False and fail_once['enabled']:
                fail_once['enabled'] = False
                raise Win32BackendError('injected second-character UP failure')
            backend.emissions += 1

        backend._send_unicode_unit = send_unicode_unit
        spec = interface()
        spec['actions']['move']['operation'] = 'text'
        observations = []
        dispatches = []
        effect_checks = []

        def observe(_request):
            row, _ = observer.get(1)
            observations.append(row['sequence'])
            return {'sequence': row['sequence'], 'captured_ns': row['capture_ns'],
                    'surface': 'win32-fixture', 'predicates': {'ready': True},
                    'evidence_ref': 'frame-1', 'evidence_digest': 'digest-1'}

        def execute(_request):
            dispatches.append(True)
            before = backend.emissions
            try:
                backend.execute({'ops': [{'op': 'text', 'text': 'AB'}]})
            except Win32ExecutionError as error:
                release = error.release_receipt
                return {'status': 'delivery_uncertain', 'action_id': 'text-1',
                        'effect_ref': 'text-effect-1',
                        'input_dispatched': backend.emissions > before,
                        'release': {'verified': release['verified'],
                                    'keys_down': release['keys_down'],
                                    'buttons_down': release['buttons_down']}}
            self.fail('injected text failure must escape the backend as an owned failure')

        receipt = run(spec, {
            'observe': observe,
            'admit': lambda request: {'eligible': True, 'status': 'revalidated',
                'authorization': 'single-use-text-permit',
                'expected_sequence': request['observation']['sequence'],
                'valid_until_ns': time.monotonic_ns() + 4_000_000_000},
            'execute': execute,
            'verify_effect': lambda request: effect_checks.append(request) or {
                'status': 'succeeded', 'evidence_ref': 'unexpected'},
            'cancelled': lambda: False,
        }, clock=time.monotonic_ns)

        self.assertEqual((receipt['outcome'], receipt['reason']),
                         ('SAFE_YIELD', 'delivery_uncertain'))
        self.assertEqual(receipt['completed_transitions'], 0)
        self.assertEqual(dispatches, [True])
        self.assertEqual(observations, [1])
        self.assertEqual(effect_checks, [])
        self.assertEqual(sends, [(ord('A'), True), (ord('A'), False),
                                 (ord('B'), True), (ord('B'), False),
                                 (ord('B'), False)])
        self.assertEqual(backend.pending_unicode_ups, set())
        self.assertEqual(backend.emissions, 4)
        terminal = next(row for row in receipt['critical_events']
                        if row['event'] == 'action_terminal')
        self.assertTrue(terminal['input_dispatched'])
        self.assertTrue(terminal['release_verified'])


if __name__ == '__main__':
    unittest.main()
