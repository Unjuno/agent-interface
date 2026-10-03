"""Session custody fence; all native effects mocked."""
import types,unittest
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.core_v1.contract import SCHEMA_PROGRAM
class SessionCustody(unittest.TestCase):
    def make(self):
        b=object.__new__(Win32Backend);b.held_keys={'SHIFT':16};b.held_buttons=set();b.emissions=0;b.targets={};self.sends=[];self.state=0
        b.user32=types.SimpleNamespace(GetAsyncKeyState=lambda vk:self.state);b._send_key=lambda vk,down:self.sends.append((vk,down));b._send=lambda *a:None
        return b,m.Win32RuntimeSession(b)
    def dispatch(self,s,ops):
        p=dict(schema=SCHEMA_PROGRAM,program_id='custody-fence-test',source=dict(observation_seq=1,binding_revision=1),authority=dict(lease_id='synthetic',expires_at_ns=1000000),terminal=dict(release_all_required=True),ops=ops)
        return s.dispatch(p,current_observation_seq=1,current_binding_revision=1,now_ns=0)
    def test_pending_custody_refuses_new_input_without_sends(self):
        b,s=self.make();r=self.dispatch(s,[dict(op='key_state',key='S',down=True),dict(op='release_all')])
        self.assertEqual(r['status'],'refused');self.assertEqual(r['error'],'RELEASE_UNVERIFIED');self.assertEqual(self.sends,[])
    def test_unverified_cleanup_keeps_fence(self):
        b,s=self.make();self.assertEqual(self.dispatch(s,[dict(op='release_all')])['status'],'release_unverified');n=len(self.sends)
        self.assertEqual(self.dispatch(s,[dict(op='key_state',key='S',down=True),dict(op='release_all')])['status'],'refused');self.assertEqual(len(self.sends),n)
    def test_release_only_confirmation_allows_next_program(self):
        b,s=self.make();self.state=1
        self.assertEqual(self.dispatch(s,[dict(op='release_all')])['status'],'completed');self.assertEqual(b.held_keys,{})
        self.assertEqual(self.dispatch(s,[dict(op='key_state',key='S',down=True),dict(op='release_all')])['status'],'completed');self.assertIn((ord('S'),True),self.sends)

from runtime.backends.win32_v1 import session as m
if __name__=='__main__':unittest.main(verbosity=2)
