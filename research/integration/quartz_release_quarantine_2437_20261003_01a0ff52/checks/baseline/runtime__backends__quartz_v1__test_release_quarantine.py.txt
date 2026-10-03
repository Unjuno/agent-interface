"""Sticky release quarantine with inert APIs and native loading forbidden."""
from __future__ import annotations

import unittest
from unittest.mock import Mock

from . import test_release_faults as original_fault_fixture
from .backend import QuartzBackendError
from .session import QuartzRuntimeSession


class QuartzReleaseQuarantineTests(unittest.TestCase):
    def setUp(self):
        fixture = original_fault_fixture.QuartzReleaseFaultTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.backend = fixture.backend
        self.cg = fixture.cg
        self.session = QuartzRuntimeSession(self.backend)

    def dispatch(self, ops=(), *, sequence=7, revision=3):
        program = self.fixture.program(list(ops))
        program['source'] = {'observation_seq': sequence, 'binding_revision': revision}
        return self.session.dispatch(program, current_observation_seq=sequence,
                                     current_binding_revision=revision, now_ns=1_000_000)

    def forbid_followup_access(self):
        calls = list(self.cg.calls)
        emissions = self.backend.emissions
        self.backend.monotonic_ns = Mock(side_effect=AssertionError('clock must not be read'))
        self.backend.manifest = Mock(side_effect=AssertionError('manifest must not be read'))
        self.backend.preflight = Mock(side_effect=AssertionError('preflight must not run'))
        self.backend.execute = Mock(side_effect=AssertionError('follow-up execution forbidden'))
        result = self.dispatch([{'op': 'key_state', 'key': 'CTRL', 'down': True}])
        self.assertEqual(result.get('error'), 'INPUT_RECOVERY_REQUIRED')
        self.assertIs(result['input_dispatched'], False)
        self.assertIs(result['recovery_required'], True)
        self.assertEqual((self.cg.calls, self.backend.emissions), (calls, emissions))
        self.backend.monotonic_ns.assert_not_called()
        self.backend.manifest.assert_not_called()
        self.backend.preflight.assert_not_called()
        self.backend.execute.assert_not_called()

    def test_real_inert_sticky_input_blocks_followup_emissions(self):
        self.cg.faults[('sticky', ('key', 0))] = True
        first = self.dispatch()
        self.assertEqual(first['status'], 'release_unverified')
        self.assertEqual(self.backend.held_keys, {'A': 0})
        before = self.backend.emissions
        calls = len(self.cg.calls)
        second = self.dispatch([{'op': 'key_state', 'key': 'CTRL', 'down': True}])
        self.assertEqual(second.get('error'), 'INPUT_RECOVERY_REQUIRED')
        self.assertEqual((self.backend.emissions, len(self.cg.calls)), (before, calls))
        self.assertNotIn(('key_create', (59, True)), self.cg.calls)

    def test_partial_execution_failure_blocks_followup(self):
        self.backend.text = Mock(side_effect=QuartzBackendError('partial text failure'))
        self.cg.faults[('sticky', ('key', 0))] = True
        first = self.dispatch([{'op': 'text', 'text': 'x'}])
        self.assertEqual(first['status'], 'execution_failed')
        self.assertIn('partial text failure', first['detail'])
        self.assertIs(first['execution']['releases'][0]['verified'], False)
        self.forbid_followup_access()

    def test_preflight_cleanup_failure_blocks_followup(self):
        self.backend.preflight.side_effect = QuartzBackendError('target lost')
        self.backend.release_all = Mock(side_effect=OSError('cleanup unavailable'))
        first = self.dispatch()
        self.assertEqual(first['error'], 'BACKEND_CONSTRAINT')
        self.assertIs(first['release']['verified'], False)
        self.backend.release_all.assert_called_once()
        self.forbid_followup_access()

    def test_backend_failure_without_release_receipt_blocks_followup(self):
        self.backend.execute = Mock(side_effect=QuartzBackendError('receipt missing'))
        first = self.dispatch()
        self.assertEqual(first['error'], 'BACKEND_EXECUTION')
        self.assertIn('receipt missing', first['detail'])
        self.forbid_followup_access()

    def test_unexpected_execution_exception_latches_before_reraise(self):
        failure = OSError('unexpected execution failure')
        self.backend.execute = Mock(side_effect=failure)
        with self.assertRaises(OSError) as caught:
            self.dispatch()
        self.assertIs(caught.exception, failure)
        self.forbid_followup_access()

    def test_malformed_or_contradictory_release_cannot_complete(self):
        releases = [None, [], [None], [{'verified': True}],
                    [{'verified': 1, 'keys_down': [], 'buttons_down': []}],
                    [{'verified': 'true', 'keys_down': [], 'buttons_down': []}],
                    [{'verified': True, 'keys_down': [], 'buttons_down': ['left']}],
                    [{'verified': True, 'keys_down': [], 'buttons_down': [], 'keys_unknown': ['A']}],
                    [{'verified': True, 'keys_down': [], 'buttons_down': [], 'errors': [{'stage': 'key_release'}]}]]
        for value in releases:
            with self.subTest(releases=value):
                session = QuartzRuntimeSession(self.backend)
                self.backend.execute = Mock(return_value={'releases': value})
                result = session.dispatch(self.fixture.program([]), current_observation_seq=7,
                                          current_binding_revision=3, now_ns=1_000_000)
                self.assertEqual(result['status'], 'release_unverified')
                self.assertIs(result['recovery_required'], True)

    def test_verified_release_allows_later_valid_dispatch(self):
        first = self.dispatch()
        self.assertEqual(first['status'], 'completed')
        second = self.dispatch([{'op': 'key_state', 'key': 'CTRL', 'down': True}])
        self.assertEqual(second['status'], 'completed')
        self.assertIn(('key_create', (59, True)), self.cg.calls)

    def test_core_refusal_does_not_block_later_valid_dispatch(self):
        refused = self.session.dispatch(self.fixture.program([]), current_observation_seq=6,
                                        current_binding_revision=3, now_ns=1_000_000)
        self.assertEqual(refused['error'], 'STALE_OBSERVATION')
        self.assertEqual(self.cg.calls, [])
        self.assertEqual(self.dispatch()['status'], 'completed')

    def test_later_explicit_backend_cleanup_does_not_clear_session(self):
        self.cg.faults[('sticky', ('key', 0))] = True
        self.assertEqual(self.dispatch()['status'], 'release_unverified')
        self.cg.faults.clear()
        self.assertIs(self.backend.release_all()['verified'], True)
        self.forbid_followup_access()

    def test_new_binding_and_observation_do_not_clear_session(self):
        self.cg.faults[('sticky', ('key', 0))] = True
        self.assertEqual(self.dispatch()['status'], 'release_unverified')
        calls = list(self.cg.calls)
        second = self.dispatch([{'op': 'key_state', 'key': 'CTRL', 'down': True}], sequence=8, revision=4)
        self.assertEqual(second.get('error'), 'INPUT_RECOVERY_REQUIRED')
        self.assertEqual(self.cg.calls, calls)

    def test_any_unverified_receipt_blocks_despite_later_verified_release(self):
        self.backend.execute = Mock(return_value={'releases': [
            {'verified': False, 'keys_down': [], 'buttons_down': []},
            {'verified': True, 'keys_down': [], 'buttons_down': []}]})
        self.assertEqual(self.dispatch()['status'], 'release_unverified')
        self.forbid_followup_access()

    def test_mutating_returned_receipt_does_not_clear_latch(self):
        receipt = {'verified': False, 'keys_down': [], 'buttons_down': []}
        self.backend.execute = Mock(return_value={'releases': [receipt]})
        self.assertEqual(self.dispatch()['status'], 'release_unverified')
        receipt['verified'] = True
        self.forbid_followup_access()


if __name__ == '__main__':
    unittest.main()
