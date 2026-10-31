import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

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
        self.owner._xauthority = '/tmp/a'
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

if __name__=='__main__': unittest.main()
