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
        down=[True];b=self.make(lambda vk:0x8000 if down[0] else 1)
        self.assertFalse(b.release_all()['verified']);down[0]=False
        self.assertTrue(b.release_all()['verified']);self.assertEqual(b.held_keys,{});self.assertEqual(b.held_buttons,set())
    def test_partial_confirmation_keeps_only_unresolved(self):
        b=self.make(lambda vk:0x8000 if vk==16 else 1)
        self.assertFalse(b.release_all()['verified']);self.assertEqual(b.held_keys,{'SHIFT':16});self.assertEqual(b.held_buttons,set())
    def test_query_exception_preserves_custody(self):
        def bad(vk):raise OSError('state unavailable')
        b=self.make(bad)
        with self.assertRaises(OSError):b.release_all()
        self.assertEqual(b.held_keys,{'SHIFT':16});self.assertEqual(b.held_buttons,{'left'})
    def test_send_exception_preserves_custody(self):
        b=self.make(lambda vk:1)
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
        b=self.make(lambda vk:1)
        b.key_state('SHIFT',False)
        self.assertEqual(b.held_keys,{})
        self.assertEqual(b.held_buttons,{'left'})
    def test_confirmed_explicit_button_up_retires_only_that_button(self):
        b=self.make(lambda vk:1)
        b.pointer_button('left',False)
        self.assertEqual(b.held_buttons,set())
        self.assertEqual(b.held_keys,{'SHIFT':16})
    def test_explicit_key_up_query_failure_preserves_custody(self):
        def bad(vk):raise OSError('state unavailable')
        b=self.make(bad)
        b.key_state('SHIFT',False)
        self.assertEqual(b.held_keys,{'SHIFT':16})
    def test_explicit_button_up_query_failure_preserves_custody(self):
        def bad(vk):raise OSError('state unavailable')
        b=self.make(bad)
        b.pointer_button('left',False)
        self.assertEqual(b.held_buttons,{'left'})
    def test_zero_release_is_unknown_not_verified(self):
        b=self.make(lambda vk:0)
        r=b.release_all()
        self.assertFalse(r['verified'])
        self.assertEqual(r['keys_unknown'],['SHIFT'])
        self.assertEqual(r['buttons_unknown'],['left'])
        self.assertEqual(b.held_keys,{'SHIFT':16})
        self.assertEqual(b.held_buttons,{'left'})
    def test_repeated_zero_remains_queryable(self):
        queries=[];b=self.make(lambda vk:queries.append(vk) or 0)
        self.assertFalse(b.release_all()['verified']);n=len(queries)
        self.assertFalse(b.release_all()['verified']);self.assertGreater(len(queries),n)
    def test_zero_explicit_key_up_keeps_custody(self):
        b=self.make(lambda vk:0);b.key_state('SHIFT',False)
        self.assertEqual(b.held_keys,{'SHIFT':16})
    def test_zero_explicit_button_up_keeps_custody(self):
        b=self.make(lambda vk:0);b.pointer_button('left',False)
        self.assertEqual(b.held_buttons,{'left'})
    def test_mixed_up_and_unknown_retire_only_confirmed_up(self):
        b=self.make(lambda vk:0 if vk==16 else 1)
        r=b.release_all();self.assertFalse(r['verified'])
        self.assertEqual(r['keys_down'],[]);self.assertEqual(r['keys_unknown'],['SHIFT'])
        self.assertEqual(r['buttons_unknown'],[])
        self.assertEqual(b.held_keys,{'SHIFT':16});self.assertEqual(b.held_buttons,set())
    def test_alias_up_uses_one_state_query(self):
        calls=[];sends=[]
        b=self.make(lambda vk:calls.append(vk) or (1 if len(calls)==1 else 0))
        b.held_keys={'CTRL':17,'CONTROL':17};b.held_buttons=set();b._send_key=lambda vk,down:sends.append((vk,down))
        self.assertTrue(b.release_all()['verified']);self.assertEqual(calls,[17]);self.assertEqual(sends,[(17,False)])
    def test_alias_unknown_retains_all_names_with_one_query(self):
        calls=[];b=self.make(lambda vk:calls.append(vk) or 0)
        b.held_keys={'CTRL':17,'CONTROL':17};b.held_buttons=set()
        r=b.release_all();self.assertFalse(r['verified']);self.assertEqual(r['keys_unknown'],['CONTROL','CTRL']);self.assertEqual(calls,[17]);self.assertEqual(len(b.held_keys),2)
    def test_alias_down_retains_all_names_with_one_query(self):
        calls=[];b=self.make(lambda vk:calls.append(vk) or 0x8000)
        b.held_keys={'CTRL':17,'CONTROL':17};b.held_buttons=set()
        r=b.release_all();self.assertFalse(r['verified']);self.assertEqual(r['keys_down'],['CONTROL','CTRL']);self.assertEqual(calls,[17]);self.assertEqual(len(b.held_keys),2)
if __name__=='__main__':
    unittest.main(verbosity=2)
