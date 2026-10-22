import time
import tempfile
import unittest
from unittest.mock import Mock

from runtime.backends.win32_v1.backend import Win32Backend
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
            return {'verified': True, 'keys_down': [], 'buttons_down': []}

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

    def execute_compiled(self, *, change_generation_before_execute=False):
        backend, observer, bridge, events = self.setup_bridge()
        call_rows = []

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
            return {'status': 'completed', 'action_id': 'move-1',
                'effect_ref': 'effect-1', 'input_dispatched': True,
                'release': {'verified': release['verified'],
                    'keys_down': release['keys_down'],
                    'buttons_down': release['buttons_down']}}

        receipt = run(interface(), {
            'observe': observe,
            'admit': admit,
            'execute': execute,
            'verify_effect': lambda request: {
                'status': 'succeeded',
                'evidence_ref': request['observation']['evidence_ref']},
            'cancelled': lambda: False,
        }, clock=time.monotonic_ns)
        return receipt, events, call_rows, observer

    def test_compiled_core_executes_against_the_same_observation_generation(self):
        receipt, events, sequences, _ = self.execute_compiled()
        self.assertEqual(receipt['outcome'], 'TASK_SUCCEEDED')
        self.assertEqual(receipt['completed_transitions'], 1)
        self.assertEqual(sequences, [1, 2])
        self.assertEqual(events, [['move', 'fixture', 3, 3], ['release']])

    def test_generation_change_after_admission_is_refused_by_live_bridge_guard(self):
        receipt, events, sequences, observer = self.execute_compiled(
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


if __name__ == '__main__':
    unittest.main()
