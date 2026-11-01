import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
from runtime.guarded_x11_v1.private_display_recovery import PrivateDisplayRecovery


class PrivateDisplayRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.display = Mock(spec=PrivateDisplayOwner)
        self.display._session = SimpleNamespace(display=':17', authority=Path('/tmp/a'))
        self.display._process = Mock()
        self.display._process.poll.return_value = None
        self.display._retired = False
        self.owner = Mock(spec=OwnedGuardedSessionOwner)
        self.owner.display_name = ':17'
        self.owner._xauthority = str(self.display._session.authority)
        self.owner._owned_display_owner = self.display
        self.owner.state = 'open'
        self.owner._process = Mock()
        self.owner._process.is_alive.return_value = True
        self.owner._cleanup_supervisor = Mock()
        self.owner._cleanup_supervisor._process = Mock()
        self.owner._cleanup_supervisor._process.is_alive.return_value = True
        self.owner.cancel_guarded.return_value = {
            'status':'cancel_unconfirmed', 'cleanup_status':'UNKNOWN',
            'owner_process_retired':True, 'release_confirmed':False,
            'replay_allowed':False,
        }
        self.display.retire.return_value = {'status':'retired'}

    def deadline(self):
        return time.monotonic_ns() + 2_000_000_000

    def test_retires_matching_owned_display_and_keeps_old_result_unknown(self):
        recovery=PrivateDisplayRecovery(self.display,self.owner)
        result=recovery.cancel_guarded('token',deadline_monotonic_ns=self.deadline())
        self.assertEqual(result['display_retirement']['status'],'retired')
        self.assertTrue(result['fresh_display_allowed'])
        self.assertFalse(result['replay_allowed'])
        self.assertFalse(result['release_confirmed'])
        self.assertIsNone(result['task_success'])
        self.assertEqual(result['cleanup_status'],'UNKNOWN')
        self.display.retire.assert_called_once()

    def test_failed_retirement_disallows_fresh_display(self):
        self.display.retire.return_value={'status':'unknown'}
        result=PrivateDisplayRecovery(self.display,self.owner).cancel_guarded('token',deadline_monotonic_ns=self.deadline())
        self.assertFalse(result['fresh_display_allowed'])
        self.assertFalse(result['replay_allowed'])

    def test_unretired_owner_disallows_fresh_display_even_if_display_exited(self):
        self.owner.cancel_guarded.return_value['owner_process_retired']=False
        result=PrivateDisplayRecovery(self.display,self.owner).cancel_guarded('token',deadline_monotonic_ns=self.deadline())
        self.assertFalse(result['fresh_display_allowed'])

    def test_same_name_but_different_owned_generation_is_rejected(self):
        other = Mock(spec=PrivateDisplayOwner)
        self.owner._owned_display_owner = other
        with self.assertRaises(ValueError):
            PrivateDisplayRecovery(self.display, self.owner)
        self.owner.cancel_guarded.assert_not_called()
        self.display.retire.assert_not_called()

    def test_unstarted_or_unavailable_owner_is_rejected(self):
        for state, alive, supervisor in (('unopened', True, True), ('open', False, True), ('open', True, False)):
            with self.subTest(state=state, alive=alive, supervisor=supervisor):
                self.owner.state = state
                self.owner._process.is_alive.return_value = alive
                self.owner._cleanup_supervisor = Mock() if supervisor else None
                if supervisor:
                    self.owner._cleanup_supervisor._process = Mock()
                    self.owner._cleanup_supervisor._process.is_alive.return_value = True
                with self.assertRaises(ValueError):
                    PrivateDisplayRecovery(self.display, self.owner)
                self.display.retire.assert_not_called()

    def test_changed_owner_binding_before_cancel_is_refused(self):
        recovery = PrivateDisplayRecovery(self.display, self.owner)
        self.owner._owned_display_owner = Mock(spec=PrivateDisplayOwner)
        result = recovery.cancel_guarded('token', deadline_monotonic_ns=self.deadline())
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['fresh_display_allowed'])
        self.owner.cancel_guarded.assert_not_called()
        self.display.retire.assert_not_called()

    def test_changed_display_process_after_cancel_is_not_retired(self):
        recovery = PrivateDisplayRecovery(self.display, self.owner)
        def cancel(*args, **kwargs):
            self.display._process = Mock()
            return {'status':'cancel_unconfirmed', 'cleanup_status':'UNKNOWN', 'owner_process_retired':True}
        self.owner.cancel_guarded.side_effect = cancel
        result = recovery.cancel_guarded('token', deadline_monotonic_ns=self.deadline())
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['fresh_display_allowed'])
        self.display.retire.assert_not_called()

    def test_unowned_display_is_rejected(self):
        self.owner._owned_display_owner = None
        with self.assertRaises(ValueError):
            PrivateDisplayRecovery(self.display, self.owner)
        self.display.retire.assert_not_called()

    def test_cancel_ack_is_not_recovery_completion(self):
        self.owner.cancel_guarded.return_value = {'status':'cancel_requested', 'release_confirmed':False}
        result = PrivateDisplayRecovery(self.display, self.owner).cancel_guarded('token', deadline_monotonic_ns=self.deadline())
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['fresh_display_allowed'])
        self.assertFalse(result['release_confirmed'])
        self.display.retire.assert_not_called()

    def test_not_active_does_not_claim_completed_recovery(self):
        self.owner.cancel_guarded.return_value = {'status':'not_active', 'input_dispatched':False}
        result = PrivateDisplayRecovery(self.display, self.owner).cancel_guarded('token', deadline_monotonic_ns=self.deadline())
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['fresh_display_allowed'])
        self.display.retire.assert_not_called()

    def test_wrong_display_binding_refuses_before_cancel_or_retirement(self):
        self.owner.display_name=':18'
        with self.assertRaises(ValueError):PrivateDisplayRecovery(self.display,self.owner)
        self.owner.cancel_guarded.assert_not_called()
        self.display.retire.assert_not_called()

    def test_successful_non_retirement_cancel_does_not_kill_display(self):
        self.owner.cancel_guarded.return_value={'status':'cancel_requested','release_confirmed':False}
        result=PrivateDisplayRecovery(self.display,self.owner).cancel_guarded('token',deadline_monotonic_ns=self.deadline())
        self.assertFalse(result['fresh_display_allowed'])
        self.display.retire.assert_not_called()

    def test_malformed_cancel_still_retires_but_cannot_authorize_fresh_display(self):
        self.owner.cancel_guarded.return_value = None
        result=PrivateDisplayRecovery(self.display,self.owner).cancel_guarded('token',deadline_monotonic_ns=self.deadline())
        self.display.retire.assert_called_once()
        self.assertFalse(result['fresh_display_allowed'])

    def test_unknown_cancel_status_retires_and_does_not_authorize_fresh_display(self):
        self.owner.cancel_guarded.return_value={'status':'unknown'}
        result=PrivateDisplayRecovery(self.display,self.owner).cancel_guarded('token',deadline_monotonic_ns=self.deadline())
        self.display.retire.assert_called_once()
        self.assertFalse(result['fresh_display_allowed'])

    def test_different_token_cannot_reuse_previous_recovery_receipt(self):
        recovery=PrivateDisplayRecovery(self.display,self.owner)
        recovery.cancel_guarded('first',deadline_monotonic_ns=self.deadline())
        result=recovery.cancel_guarded('second',deadline_monotonic_ns=self.deadline())
        self.assertFalse(result['fresh_display_allowed'])
        self.assertEqual(result['reason'],'recovery_already_used')
        self.owner.cancel_guarded.assert_called_once()

    def test_late_display_retirement_does_not_authorize_fresh_display(self):
        recovery=PrivateDisplayRecovery(self.display,self.owner)
        with patch('runtime.guarded_x11_v1.private_display_recovery.time.monotonic_ns',
                   side_effect=[100,101,102,201]):
            result=recovery.cancel_guarded('token',deadline_monotonic_ns=200)
        self.assertFalse(result['fresh_display_allowed'])
        self.assertEqual(result['reason'],'deadline_after_display_retire')
        self.assertEqual(result['display_retirement']['status'],'retired')

    def test_late_cancellation_is_not_reported_completed(self):
        self.owner.cancel_guarded.return_value={'status':'cancel_requested'}
        recovery=PrivateDisplayRecovery(self.display,self.owner)
        with patch('runtime.guarded_x11_v1.private_display_recovery.time.monotonic_ns',
                   side_effect=[100,101,201]):
            result=recovery.cancel_guarded('token',deadline_monotonic_ns=200)
        self.assertEqual(result['status'],'unknown')
        self.assertEqual(result['reason'],'deadline_after_cancel')
        self.assertFalse(result['fresh_display_allowed'])
        self.display.retire.assert_not_called()

if __name__=='__main__': unittest.main()
