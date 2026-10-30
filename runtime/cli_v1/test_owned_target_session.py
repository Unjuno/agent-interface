import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.owned_target_session import OwnedTargetGuardedSessionOwner


class OwnedTargetSessionTests(unittest.TestCase):
    def test_prestarted_identity_accepts_child_session_after_startup(self):
        target = Mock(spec=__import__('runtime.guarded_x11_v1.owned_target_process',
                                      fromlist=['OwnedTargetProcess']).OwnedTargetProcess)
        target.running = True
        def parent_init(owner, *args, **kwargs):
            owner.session_id = 'parent-session'
            owner.display_name = ':99'
        def start(owner):
            owner.session_id = 'child-session'
        def bind(supervisor, session_id, display, xid):
            self.assertIn(supervisor._expected_session_id, (None, session_id))
            return {'status':'bound'}
        target.bind_x11_target_prestarted.side_effect = bind
        with patch.object(OwnedGuardedSessionOwner, '__init__', parent_init), \
             patch.object(OwnedGuardedSessionOwner, '_ensure_started', start), \
             patch('runtime.cli_v1.owned_target_session.PrestartedCancellationSupervisor') as factory:
            factory.side_effect = lambda worker, expected_session_id=None: Mock(
                _expected_session_id=expected_session_id)
            owner = OwnedTargetGuardedSessionOwner(
                {'app':77}, '/tmp', owned_target_process=target,
                prestarted_target_identity=True)
            owner._ensure_started()
        self.assertEqual(owner._owned_target_binding['status'], 'bound')

    def test_retire_target_precedes_existing_release_cleanup_and_is_cached(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        target = Mock()
        target.retire_bound_target.return_value = {
            'status':'retired', 'target_identity_verified':True,
            'process_exit_verified':True}
        owner._owned_target_process = target
        owner._owned_target_retirement = None
        order = []

        def base_cleanup(_self, retirement, **kwargs):
            order.append(('base_cleanup', retirement, kwargs))
            return {'status':'disconnected'}, {'status':'readback_verified'}

        retire = target.retire_bound_target
        retire.side_effect = lambda: (order.append(('target_retire',)) or {
            'status':'retired', 'target_identity_verified':True,
            'process_exit_verified':True})
        with patch.object(OwnedGuardedSessionOwner,
                          '_cleanup_after_owner_retirement', base_cleanup):
            first = owner._cleanup_after_owner_retirement(
                {'retired':True}, retry_after_resume=True)
            second = owner._cleanup_after_owner_retirement(
                {'retired':True}, retry_after_resume=True)

        self.assertEqual(order[0], ('target_retire',))
        self.assertEqual(order[1][0], 'base_cleanup')
        self.assertEqual(order[2][0], 'base_cleanup')
        self.assertEqual(first, ({'status':'disconnected'},
                                 {'status':'readback_verified'}))
        self.assertEqual(second, first)
        target.close.assert_called_once_with()
        self.assertEqual(owner._owned_target_retirement['status'], 'retired')

    def test_failed_control_owner_retirement_does_not_signal_target(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        target = Mock()
        owner._owned_target_process = target
        owner._owned_target_retirement = None
        with patch.object(OwnedGuardedSessionOwner,
                          '_cleanup_after_owner_retirement',
                          return_value=({'status':'unknown'},
                                        {'status':'not_attempted'})):
            owner._cleanup_after_owner_retirement({'retired':False})
        target.retire_bound_target.assert_not_called()
        self.assertIsNone(owner._owned_target_retirement)
        target.retire_bound_target.return_value = {'status':'retired',
                                                  'process_exit_verified':True}
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement',
                          return_value=({}, {})):
            owner._cleanup_after_owner_retirement({'retired':True})
        target.retire_bound_target.assert_called_once_with()

    def test_target_retirement_exception_does_not_skip_release_cleanup(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_process = Mock()
        owner._owned_target_process.retire_bound_target.side_effect = OSError('failed')
        owner._owned_target_retirement = None
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement',
                          return_value=({'status':'disconnected'},
                                        {'status':'readback_verified'})) as cleanup:
            owner._cleanup_after_owner_retirement({'retired':True})
        cleanup.assert_called_once()
        self.assertEqual(owner._owned_target_retirement['status'], 'unknown')
        self.assertFalse(owner._owned_target_retirement['process_exit_verified'])

    def test_cancel_preserves_unknown_and_attaches_target_receipt(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_binding = {'status':'bound', 'xid':77}
        owner._owned_target_retirement = {'status':'retired',
                                          'process_exit_verified':True}
        with patch.object(OwnedGuardedSessionOwner, 'cancel_guarded',
                          return_value={'status':'cancel_unconfirmed',
                              'cleanup_status':'UNKNOWN', 'release_confirmed':False,
                              'task_success':None, 'replay_allowed':False}):
            result = owner.cancel_guarded('call-1')
        self.assertEqual(result['owned_target_binding']['xid'], 77)
        self.assertEqual(result['owned_target_retirement']['status'], 'retired')
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertFalse(result['release_confirmed'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_close_includes_target_receipt_without_upgrading_unknown(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_binding = {'status':'bound', 'xid':77}
        owner._owned_target_retirement = {'status':'unknown',
                                          'process_exit_verified':False}
        with patch.object(OwnedGuardedSessionOwner, 'close',
                          return_value={'status':'cleanup_failed',
                              'cleanup_status':'UNKNOWN', 'task_success':None,
                              'replay_allowed':False}):
            result = owner.close()
        self.assertEqual(result['owned_target_retirement']['status'], 'unknown')
        self.assertFalse(result['owned_target_retirement']['process_exit_verified'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])


if __name__ == '__main__':
    unittest.main()
