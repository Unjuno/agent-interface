"""Tracked release custody regressions; all native calls mocked."""
import pathlib,sys,types,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[3]))
from runtime.backends.win32_v1 import backend as m
class ReleaseCustody(unittest.TestCase):
    def make(self,state):
        b=object.__new__(m.Win32Backend);b.held_keys={'SHIFT':16};b.held_buttons={'left'};b.user32=types.SimpleNamespace(GetAsyncKeyState=state);b._send_key=lambda *a:None;b._send=lambda *a:None;return b
    def test_unresolved_remains_queryable_on_second_release(self):
        queries=[]
        b=self.make(lambda vk:queries.append(vk) or 0x8000)
        self.assertFalse(b.release_all()['verified']);n=len(queries)
        self.assertFalse(b.release_all()['verified']);self.assertGreater(len(queries),n);self.assertEqual(b.held_keys,{'SHIFT':16});self.assertEqual(b.held_buttons,{'left'})
    def test_confirmed_up_retires_tracking(self):
        down=[True];b=self.make(lambda vk:0x8000 if down[0] else 0)
        self.assertFalse(b.release_all()['verified']);down[0]=False
        self.assertTrue(b.release_all()['verified']);self.assertEqual(b.held_keys,{});self.assertEqual(b.held_buttons,set())
    def test_partial_confirmation_keeps_only_unresolved(self):
        b=self.make(lambda vk:0x8000 if vk==16 else 0)
        self.assertFalse(b.release_all()['verified']);self.assertEqual(b.held_keys,{'SHIFT':16});self.assertEqual(b.held_buttons,set())
    def test_query_exception_preserves_custody(self):
        def bad(vk):raise OSError('state unavailable')
        b=self.make(bad)
        with self.assertRaises(OSError):b.release_all()
        self.assertEqual(b.held_keys,{'SHIFT':16});self.assertEqual(b.held_buttons,{'left'})
    def test_send_exception_preserves_custody(self):
        b=self.make(lambda vk:0)
        def bad(*a):raise OSError('send unavailable')
        b._send=bad
        with self.assertRaises(OSError):b.release_all()
        self.assertEqual(b.held_keys,{'SHIFT':16});self.assertEqual(b.held_buttons,{'left'})
    def test_explicit_key_up_preserves_release_obligation(self):
        b=self.make(lambda vk:0x8000)
        b.key_state('SHIFT',False)
        self.assertFalse(b.release_all()['verified'])
        self.assertEqual(b.held_keys,{'SHIFT':16})
    def test_explicit_button_up_preserves_release_obligation(self):
        b=self.make(lambda vk:0x8000)
        b.pointer_button('left',False)
        self.assertFalse(b.release_all()['verified'])
        self.assertEqual(b.held_buttons,{'left'})
    def test_key_chord_preserves_release_obligation(self):
        b=self.make(lambda vk:0x8000)
        b.held_keys={};b.held_buttons=set()
        b.key_chord(['CTRL','S'])
        self.assertFalse(b.release_all()['verified'])
        self.assertEqual(set(b.held_keys),{'CTRL','S'})
    def test_confirmed_explicit_key_up_retires_only_that_key(self):
        b=self.make(lambda vk:0)
        b.key_state('SHIFT',False)
        self.assertEqual(b.held_keys,{})
        self.assertEqual(b.held_buttons,{'left'})
    def test_confirmed_explicit_button_up_retires_only_that_button(self):
        b=self.make(lambda vk:0)
        b.pointer_button('left',False)
        self.assertEqual(b.held_buttons,set())
        self.assertEqual(b.held_keys,{'SHIFT':16})
    def test_explicit_key_up_query_failure_preserves_custody(self):
        def bad(vk):raise OSError('state unavailable')
        b=self.make(bad)
        with self.assertRaises(OSError):b.key_state('SHIFT',False)
        self.assertEqual(b.held_keys,{'SHIFT':16})
    def test_explicit_button_up_query_failure_preserves_custody(self):
        def bad(vk):raise OSError('state unavailable')
        b=self.make(bad)
        with self.assertRaises(OSError):b.pointer_button('left',False)
        self.assertEqual(b.held_buttons,{'left'})
if __name__=='__main__':
    unittest.main(verbosity=2)
