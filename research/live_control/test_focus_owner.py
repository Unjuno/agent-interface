import contextlib,io,time,unittest
import session_v6
from input_owner_v2 import InputOwner
from lease import Lease
from executor_v3 import DecisionRequired

class FocusContract(unittest.TestCase):
    def test_hold_release_and_revocation_survive_focus_return(self):
        s=None;owner=None
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                s=session_v6.suite.Session()
                session_v6.suite.prepare(s,'xterm',930301,'')
                owner=InputOwner(s.name)
            X=session_v6.suite.base.X
            original=s.d.get_input_focus().focus
            sink=s.d.screen().root.create_window(0,0,100,80,0,s.d.screen().root_depth,override_redirect=True)
            sink.map();s.d.sync()
            lease=Lease(time.perf_counter_ns()+2_000_000_000);lease.expected_focus=original.id
            owner.call('down',lease,'Control_L')
            code=s.d.keysym_to_keycode(session_v6.suite.base.XK.string_to_keysym('Control_L'))
            def down():return bool(s.d.query_keymap()[code//8]&(1<<(code%8)))
            self.assertTrue(down())
            sink.set_input_focus(X.RevertToParent,X.CurrentTime);s.d.sync()
            limit=time.perf_counter()+1
            while down() and time.perf_counter()<limit:time.sleep(.002)
            self.assertFalse(down())
            while not any(r['reason']=='focus_changed' for r in owner.records) and time.perf_counter()<limit:time.sleep(.002)
            self.assertTrue(any(r['reason']=='focus_changed' and r['verified'] for r in owner.records))
            original.set_input_focus(X.RevertToParent,X.CurrentTime);s.d.sync()
            with self.assertRaises(DecisionRequired):owner.call('down',lease,'Control_L')
            fresh=Lease(time.perf_counter_ns()+2_000_000_000);fresh.expected_focus=original.id
            owner.call('down',fresh,'Control_L');self.assertTrue(down())
            owner.call('release',fresh);self.assertFalse(down())
        finally:
            if owner is not None:owner.close()
            if s is not None:s.close()

if __name__=='__main__':unittest.main()
