"""Actual Win32 methods with inert endpoints; construction/native DLL forbidden."""
import json
import unittest
from unittest.mock import patch
from runtime.backends.win32_v1 import backend as native
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.backends.win32_v1.test_release_ledger import InertAPI
from runtime.core_v1.contract import SCHEMA_PROGRAM


class UnknownReleaseTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(native.Win32Backend, '__init__',
                                      side_effect=AssertionError('constructor forbidden')))
        self.enterContext(patch.object(native.ctypes, 'WinDLL', create=True,
                                      side_effect=AssertionError('native DLL forbidden')))
        self.enterContext(patch.object(native.time, 'sleep', return_value=None))

    def backend(self, state=0):
        backend = native.Win32Backend.__new__(native.Win32Backend)
        backend.held_keys = {'SHIFT':16}
        backend.held_buttons = {'left'}
        backend.pending_unicode_ups = set()
        backend.emissions = 0
        backend.user32 = InertAPI()
        backend.user32.GetAsyncKeyState = lambda vk:state
        return backend

    def test_zero_never_retires_tracked_key_or_button(self):
        backend=self.backend()
        for attempt in range(2):
            release=backend.release_all()
            print(json.dumps({'case':'zero-state','attempt':attempt,'release':release,
                              'held_keys':backend.held_keys,
                              'held_buttons':sorted(backend.held_buttons)}),flush=True)
            self.assertFalse(release['verified'])
            self.assertEqual(release['keys_down'],[])
            self.assertEqual(release['buttons_down'],[])
            self.assertEqual(release['keys_unknown'],['SHIFT'])
            self.assertEqual(release['buttons_unknown'],['left'])
            self.assertEqual(backend.held_keys,{'SHIFT':16})
            self.assertEqual(backend.held_buttons,{'left'})

    def test_explicit_unknown_up_refuses_following_input(self):
        for kind in ('key','button'):
            with self.subTest(kind=kind):
                backend=self.backend()
                with self.assertRaisesRegex(native.Win32BackendError,'state.*unknown'):
                    if kind=='key': backend.key_state('SHIFT',False)
                    else: backend.pointer_button('left',False)
                self.assertEqual(backend.held_keys,{'SHIFT':16})
                self.assertEqual(backend.held_buttons,{'left'})

    def test_nonzero_up_sample_can_retire_tracking(self):
        backend=self.backend(1)
        release=backend.release_all()
        self.assertTrue(release['verified'])
        self.assertEqual(backend.held_keys,{})
        self.assertEqual(backend.held_buttons,set())

    def test_aliases_share_one_physical_query_and_unknown_result(self):
        backend=self.backend()
        backend.held_keys={'CONTROL':17,'CTRL':17}; backend.held_buttons=set()
        queries=[]
        backend.user32.GetAsyncKeyState=lambda vk:queries.append(vk) or 0
        release=backend.release_all()
        self.assertEqual(queries,[17])
        self.assertEqual(release['keys_unknown'],['CONTROL','CTRL'])
        self.assertEqual(len(backend.user32.sends),1)
        self.assertEqual(len(backend.held_keys),2)

    def test_session_recovery_requires_nonzero_confirmation_and_never_replays(self):
        backend=self.backend(); session=Win32RuntimeSession(backend)
        program={'schema':SCHEMA_PROGRAM,'program_id':'release-only',
                 'source':{'observation_seq':7,'binding_revision':3},
                 'authority':{'lease_id':'inert','expires_at_ns':100},
                 'terminal':{'release_all_required':True},'ops':[{'op':'release_all'}]}
        first=session.dispatch(program,current_observation_seq=7,current_binding_revision=3,now_ns=1)
        print(json.dumps({'case':'session-zero','reply':first}),flush=True)
        self.assertEqual(first['status'],'release_unverified')
        self.assertTrue(session.recovery_required)
        sent=len(backend.user32.sends)
        refused=session.dispatch(program,current_observation_seq=7,current_binding_revision=3,now_ns=1)
        self.assertEqual(refused['error'],'INPUT_RECOVERY_REQUIRED')
        self.assertEqual(len(backend.user32.sends),sent)
        failed=session.recover_input()
        self.assertEqual(failed['status'],'recovery_failed')
        self.assertTrue(session.recovery_required)
        backend.user32.GetAsyncKeyState=lambda vk:1
        recovered=session.recover_input()
        self.assertEqual(recovered['status'],'input_recovered')
        self.assertFalse(session.recovery_required)
        self.assertIsNone(recovered['task_success'])
        self.assertIs(recovered['replay_allowed'],False)


if __name__=='__main__': unittest.main()
