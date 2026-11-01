import unittest
import threading
from unittest.mock import Mock, patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class DeadOwnerCancelTests(unittest.TestCase):
    def test_closed_dead_owner_remains_inactive_without_cleanup(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._cancel_transaction_lock=threading.Lock()
        owner._process=Mock();owner._process.is_alive.return_value=False
        owner._control=Mock();owner.state='closed';owner._control_lock=Mock()
        owner._retire=Mock();owner._cleanup_after_owner_retirement=Mock()
        result=owner.cancel_guarded('op')
        self.assertEqual(result['status'],'not_active')
        owner._control.send.assert_not_called()
        owner._retire.assert_not_called();owner._cleanup_after_owner_retirement.assert_not_called()

    def test_dead_owner_keeps_obligation_and_unconfirmed_cleanup(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
        owner._cancel_transaction_lock=threading.Lock()
        owner._process = Mock()
        owner._process.is_alive.return_value = False
        owner._process.exitcode = -15
        owner._control = Mock()
        owner.state = 'open'
        owner._execution_unknown = False
        owner.review_required = False
        owner._retire = Mock(return_value={'retired': True, 'exitcode': -15})
        owner._owner_input_obligations_state = object()
        owner._owner_input_obligations = {'keys': {}, 'buttons': []}
        owner._owner_input_obligations_source = 'parent_initial_state'
        owner._owner_input_obligations_live_read = {'status': 'not_read'}
        owner._cleanup_after_owner_retirement = Mock()
        snapshot = {'status': 'snapshot', 'obligations': {'keys': {'a': 38}, 'buttons': []}}
        with patch('runtime.cli_v1.owned_guarded_session._read_owner_input_obligations',
                   return_value=snapshot):
            result = owner.cancel_guarded('op')
        self.assertEqual(result['status'], 'cancel_unconfirmed')
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertFalse(result['release_confirmed'])
        self.assertFalse(result['replay_allowed'])
        self.assertEqual(result['owner_input_obligations'], snapshot['obligations'])
        self.assertTrue(owner.review_required)
        owner._cleanup_after_owner_retirement.assert_not_called()

    def test_dead_owner_does_not_erase_prior_disconnect_evidence(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._cancel_transaction_lock=threading.Lock()
        owner._process=Mock();owner._process.is_alive.return_value=False;owner._process.exitcode=-15
        owner._control=Mock();owner.state='open';owner._retirement={'retired':True,'exitcode':-15}
        owner._owner_client_disconnect={'status':'disconnected','worker_retired':True}
        owner._owner_release_attempt=None;owner._owner_input_obligations_state=None
        owner._owner_input_obligations={'keys':{},'buttons':[]}
        owner._owner_input_obligations_source='parent_initial_state'
        owner._owner_input_obligations_live_read={'status':'not_read'}
        result=owner.cancel_guarded('op')
        self.assertEqual(result['owner_client_disconnect'],{'status':'disconnected','worker_retired':True})
        self.assertEqual(result['owner_release_attempt']['status'],'not_attempted')
        self.assertFalse(result['release_confirmed'])


if __name__ == '__main__':
    unittest.main()
