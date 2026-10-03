import unittest
import time
from runtime.backends.win32_v1.backend import Win32Backend,Win32BackendError
import runtime.guarded_win32_v1.test_late_state as fixtures

class UnicodeNeutralCase(unittest.TestCase):
    def test_late_pending_consumes_permission_then_explicit_recovery(self):
        backend,observer,bridge,raw,events=fixtures.Cases('test_exact_expiry_consumes_without_capture').fixture()
        permit=bridge.prepare('button',[1,1])
        backend.pending_unicode_ups={65};backend.held_keys={'CTRL':17}
        count=backend._capture_hdc.call_count
        result=bridge.execute(permit['authorization'])
        self.assertEqual(result['status'],'refused')
        self.assertEqual(backend._capture_hdc.call_count,count)
        self.assertEqual(events,[])
        self.assertTrue(bridge.session.recovery_required)
        backend.user32.GetAsyncKeyState.return_value=0
        sends=[];failed=[True]
        def unicode_up(unit,down):
            sends.append(['unicode',unit,down])
            if failed[0]:raise Win32BackendError('injected Unicode UP failure')
        backend._send_unicode_unit=unicode_up
        backend._send_key=lambda vk,down:sends.append(['key',vk,down])
        backend.release_all=Win32Backend.release_all.__get__(backend)
        first=bridge.recover_input()
        self.assertEqual(first['status'],'recovery_failed')
        self.assertEqual(sends,[['unicode',65,False],['key',17,False]])
        self.assertEqual(backend.pending_unicode_ups,{65})
        self.assertEqual(backend.held_keys,{})
        self.assertTrue(bridge.session.recovery_required)
        with self.assertRaisesRegex(ValueError,'recovery required'):bridge.prepare('button',[1,1])
        failed[0]=False
        second=bridge.recover_input()
        self.assertEqual(second['status'],'input_recovered')
        self.assertIsNone(second['task_success'])
        self.assertFalse(second['replay_allowed'])
        self.assertEqual(sends,[['unicode',65,False],['key',17,False],['unicode',65,False]])
        self.assertFalse(backend.pending_unicode_ups)
        self.assertFalse(bridge.session.recovery_required)
        self.assertEqual(bridge.execute(permit['authorization'])['error'],'AUTHORIZATION_CONSUMED_OR_UNKNOWN')
        self.assertFalse(bridge.lock.locked())

    def test_pending_after_movement_keeps_effect_unknown(self):
        backend,observer,bridge,raw,events=fixtures.Cases('test_exact_expiry_consumes_without_capture').fixture()
        permit=bridge.prepare('button',[1,1]);base=backend.pointer_move
        backend.pending_unicode_ups=set()
        def move(*args):base(*args);backend.pending_unicode_ups.add(65)
        backend.pointer_move=move;called=[]
        result=bridge.execute(permit['authorization'],verify_effect=lambda *args:called.append(True),effect_deadline_ns=time.monotonic_ns()+1_000_000_000)
        self.assertEqual(result['status'],'completed')
        self.assertIsNone(result['task_success'])
        self.assertTrue(result['recovery_required'])
        self.assertEqual(called,[])
        self.assertEqual(events,[['move','fixture',3,3],['release']])

    def test_pending_unicode_refuses_preparation(self):
        backend,observer,bridge,raw,events=fixtures.Cases('test_exact_expiry_consumes_without_capture').fixture()
        backend.pending_unicode_ups={65}
        count=backend._capture_hdc.call_count
        with self.assertRaisesRegex(ValueError,'input neutrality unavailable'):
            bridge.prepare('button',[1,1])
        self.assertEqual(backend._capture_hdc.call_count,count)
        self.assertTrue(bridge.session.recovery_required)
        self.assertFalse(bridge.permits)
        self.assertEqual(events,[])

if __name__=='__main__':unittest.main()
