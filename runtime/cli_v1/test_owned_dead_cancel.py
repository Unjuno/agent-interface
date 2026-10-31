import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class DeadOwnerCancelTests(unittest.TestCase):
    def test_dead_owner_keeps_obligation_and_unconfirmed_cleanup(self):
        owner = object.__new__(OwnedGuardedSessionOwner)
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


if __name__ == '__main__':
    unittest.main()
