import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from input_owner_generation_protocol_v1 import InputOwnerGenerationProtocol


class FakeOwner:
    def __init__(self, identifier):
        self.owner_id = identifier


class FakeBackend:
    def __init__(self, fail=False):
        self._owner_generation = 0
        self.owner = FakeOwner('owner-0')
        self.calls = []
        self.fail = fail
        self.snapshot_failures = 0
        self.sequence = 4
        self._source_identity = None
        self.observed_pointer = {'focus': 9, 'surface': 17}
        self.observed_focus = 9

    def rotate_input_owner_after_cancel(self, terminal):
        self.calls.append(('rotate', terminal['id']))
        if self.fail:
            raise ValueError('rotation refused')
        self._owner_generation += 1
        old = self.owner.owner_id
        self.owner = FakeOwner(f'owner-{self._owner_generation}')
        return {'event': 'input_owner_generation', 'terminal_id': terminal['id'],
                'generation': self._owner_generation,
                'previous_generation': terminal['input_owner_generation'],
                'previous_owner_id': old,
                'owner_id': self.owner.owner_id, 'source_invalidated': True,
                'grants_input_authority': False}

    def snapshot(self, identifier, index):
        self.calls.append(('snapshot', identifier, index))
        if self.snapshot_failures:
            self.snapshot_failures -= 1
            raise RuntimeError('synthetic passive capture failure')
        self.sequence += 1
        self._source_identity = (self.sequence, self.observed_pointer['surface'], 'd' * 64)


class FakeExecutor:
    def __init__(self, events, backend=None):
        self.events, self.backend = events, backend
        self.closed = False

    def close(self):
        self.events.append('executor-close')
        self.closed = True


class OwnerGenerationProtocolTests(unittest.TestCase):
    def test_latest_cancel_terminal_closes_rotates_then_recreates_executor(self):
        protocol, backend, events = InputOwnerGenerationProtocol(), FakeBackend(), []
        first = {'event': 'terminal', 'id': 'cancel-1', 'status': 'cancelled'}
        protocol.record_terminal(first, backend)
        self.assertEqual(first['input_owner_generation'], 0)
        self.assertEqual(first['input_owner_id'], 'owner-0')
        created = []

        def factory(selected_backend):
            events.append('executor-create')
            value = FakeExecutor(events, selected_backend)
            created.append(value)
            return value

        replacement, receipt = protocol.rotate(
            {'op': 'rotate_input_owner', 'id': 'cancel-1'},
            executor=FakeExecutor(events), backend=backend, executor_factory=factory)
        self.assertEqual(events, ['executor-close', 'executor-create'])
        self.assertIs(replacement, created[0])
        self.assertEqual(backend.calls, [('rotate', 'cancel-1')])
        self.assertEqual(receipt['generation'], 1)
        self.assertFalse(receipt['grants_input_authority'])
        refreshed = protocol.refresh_source(
            {'op': 'refresh_owner_source', 'id': 'cancel-1'}, backend=backend)
        self.assertEqual(refreshed['event'], 'input_owner_source_refreshed')
        self.assertEqual(refreshed['sequence'], backend.sequence)
        self.assertEqual(refreshed['digest'], 'd' * 64)
        self.assertFalse(refreshed['grants_input_authority'])
        self.assertIsNone(protocol._refresh_required)
        self.assertEqual(backend.calls[-1], ('snapshot', 'owner-generation-source-1-1', 0))

    def test_source_refresh_is_exact_one_shot_and_follows_rotation(self):
        protocol, backend = InputOwnerGenerationProtocol(), FakeBackend()
        with self.assertRaisesRegex(ValueError, 'matching post-rotation'):
            protocol.refresh_source({'op': 'refresh_owner_source', 'id': 'before'},
                                    backend=backend)
        protocol.record_terminal({'event': 'terminal', 'id': 'cancel-1'}, backend)
        replacement, _ = protocol.rotate(
            {'op': 'rotate_input_owner', 'id': 'cancel-1'},
            executor=FakeExecutor([]), backend=backend,
            executor_factory=lambda _backend: FakeExecutor([]))
        result = protocol.refresh_source(
            {'op': 'refresh_owner_source', 'id': 'cancel-1'}, backend=backend)
        self.assertEqual(result['generation'], 1)
        with self.assertRaisesRegex(ValueError, 'matching post-rotation'):
            protocol.refresh_source({'op': 'refresh_owner_source', 'id': 'cancel-1'},
                                    backend=backend)
        self.assertFalse(replacement.closed)

    def test_source_refresh_has_four_attempt_ceiling_and_preserves_invalid_source(self):
        protocol, backend = InputOwnerGenerationProtocol(), FakeBackend()
        protocol.record_terminal({'event': 'terminal', 'id': 'cancel-1'}, backend)
        executor = FakeExecutor([])
        protocol.rotate({'op': 'rotate_input_owner', 'id': 'cancel-1'},
                        executor=executor, backend=backend,
                        executor_factory=lambda _backend: FakeExecutor([]))
        backend.snapshot_failures = protocol.MAX_REFRESH_ATTEMPTS
        for _ in range(protocol.MAX_REFRESH_ATTEMPTS):
            with self.assertRaisesRegex(RuntimeError, 'synthetic passive capture failure'):
                protocol.refresh_source({'op': 'refresh_owner_source', 'id': 'cancel-1'},
                                        backend=backend)
            self.assertIsNone(backend._source_identity)
        with self.assertRaisesRegex(ValueError, 'refresh limit exhausted'):
            protocol.refresh_source({'op': 'refresh_owner_source', 'id': 'cancel-1'},
                                    backend=backend)
        self.assertEqual(protocol._refresh_attempts, 4)
        self.assertIsNotNone(protocol._refresh_required)
        self.assertEqual(sum(call[0] == 'snapshot' for call in backend.calls), 4)

    def test_stale_terminal_is_refused_before_closing_executor(self):
        protocol, backend, events = InputOwnerGenerationProtocol(), FakeBackend(), []
        protocol.record_terminal({'event': 'terminal', 'id': 'cancel-1'}, backend)
        protocol.record_terminal({'event': 'terminal', 'id': 'later'}, backend)
        executor = FakeExecutor(events)
        with self.assertRaisesRegex(ValueError, 'latest published terminal'):
            protocol.rotate({'op': 'rotate_input_owner', 'id': 'cancel-1'},
                            executor=executor, backend=backend,
                            executor_factory=lambda _backend: self.fail('must not recreate'))
        self.assertFalse(executor.closed)
        self.assertEqual(backend.calls, [])

    def test_rotation_failure_keeps_executor_closed_and_creates_no_replacement(self):
        protocol, backend, events = InputOwnerGenerationProtocol(), FakeBackend(fail=True), []
        protocol.record_terminal({'event': 'terminal', 'id': 'cancel-1'}, backend)
        executor = FakeExecutor(events)
        with self.assertRaisesRegex(RuntimeError, 'failed closed'):
            protocol.rotate({'op': 'rotate_input_owner', 'id': 'cancel-1'},
                            executor=executor, backend=backend,
                            executor_factory=lambda _backend: self.fail('must not recreate'))
        self.assertTrue(executor.closed)
        self.assertEqual(events, ['executor-close'])

    def test_malformed_receipt_closes_replacement_and_fails_closed(self):
        protocol, backend, events = InputOwnerGenerationProtocol(), FakeBackend(), []
        backend.rotate_input_owner_after_cancel = lambda _terminal: {'event': 'wrong'}
        protocol.record_terminal({'event': 'terminal', 'id': 'cancel-1'}, backend)
        executor = FakeExecutor(events)
        with self.assertRaisesRegex(RuntimeError, 'receipt invalid'):
            protocol.rotate({'op': 'rotate_input_owner', 'id': 'cancel-1'},
                            executor=executor, backend=backend,
                            executor_factory=lambda _backend: FakeExecutor(events))
        self.assertTrue(executor.closed)
        self.assertEqual(events, ['executor-close', 'executor-close'])


if __name__ == '__main__':
    unittest.main()
