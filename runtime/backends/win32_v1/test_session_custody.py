"""Session custody fence; all native effects mocked."""
import types,unittest
from unittest.mock import patch
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.core_v1.contract import SCHEMA_PROGRAM
class SessionCustody(unittest.TestCase):
    def make(self):
        b=object.__new__(Win32Backend);b.held_keys={'SHIFT':16};b.held_buttons=set();b.pending_unicode_ups=set();b.emissions=0;b.targets={};self.sends=[];self.state=0
        b.user32=types.SimpleNamespace(GetAsyncKeyState=lambda vk:self.state);b._send_key=lambda vk,down:self.sends.append((vk,down));b._send=lambda *a:None
        return b,m.Win32RuntimeSession(b)
    def dispatch(self,s,ops):
        p=dict(schema=SCHEMA_PROGRAM,program_id='custody-fence-test',source=dict(observation_seq=1,binding_revision=1),authority=dict(lease_id='synthetic',expires_at_ns=1000000),terminal=dict(release_all_required=True),ops=ops)
        return s.dispatch(p,current_observation_seq=1,current_binding_revision=1,now_ns=0)
    def test_pending_custody_refuses_new_input_without_sends(self):
        b,s=self.make();r=self.dispatch(s,[dict(op='key_state',key='S',down=True),dict(op='release_all')])
        self.assertEqual(r['status'],'refused');self.assertEqual(r['error'],'RELEASE_UNVERIFIED');self.assertEqual(self.sends,[])

    def test_pending_unicode_release_refuses_new_input(self):
        b,s=self.make();b.held_keys={};b.pending_unicode_ups={65}
        r=self.dispatch(s,[dict(op='key_state',key='S',down=True),dict(op='release_all')])
        self.assertEqual(r['status'],'refused');self.assertEqual(r['error'],'RELEASE_UNVERIFIED');self.assertEqual(self.sends,[])
    def test_unverified_cleanup_keeps_fence(self):
        b,s=self.make();self.assertEqual(self.dispatch(s,[dict(op='release_all')])['status'],'release_unverified');n=len(self.sends)
        self.assertEqual(self.dispatch(s,[dict(op='key_state',key='S',down=True),dict(op='release_all')])['status'],'refused');self.assertEqual(len(self.sends),n)
    def test_release_only_confirmation_allows_next_program(self):
        b,s=self.make();self.state=1
        self.assertEqual(self.dispatch(s,[dict(op='release_all')])['status'],'completed');self.assertEqual(b.held_keys,{})
        self.assertEqual(self.dispatch(s,[dict(op='key_state',key='S',down=True),dict(op='release_all')])['status'],'completed');self.assertIn((ord('S'),True),self.sends)

    def test_unverified_key_up_aborts_remaining_ops_in_same_program(self):
        b,s=self.make();self.state=0;b.held_keys={}
        events=[]
        b.manifest=lambda:{'capabilities':{}}
        b.preflight=lambda program:None
        b.text=lambda value:events.append(('text',value))
        accepted=types.SimpleNamespace(accepted=True,error=None,required_capabilities=[])
        with patch.object(m,'admit_program',return_value=accepted):
            r=self.dispatch(s,[dict(op='key_state',key='SHIFT',down=True),
                               dict(op='key_state',key='SHIFT',down=False),
                               dict(op='text',text='SHOULD NOT SEND'),
                               dict(op='release_all')])
        self.assertEqual(r['status'],'release_unverified')
        self.assertEqual(events,[])
        self.assertEqual(self.sends,[(16,True),(16,False),(16,False)])
        self.assertEqual(b.held_keys,{'SHIFT':16})

    def test_unverified_chord_completion_aborts_remaining_ops(self):
        b,s=self.make();self.state=0;b.held_keys={}
        events=[]
        b.manifest=lambda:{'capabilities':{}}
        b.preflight=lambda program:None
        b.text=lambda value:events.append(('text',value))
        accepted=types.SimpleNamespace(accepted=True,error=None,required_capabilities=[])
        with patch.object(m,'admit_program',return_value=accepted):
            r=self.dispatch(s,[dict(op='key_chord',keys=['CTRL','S']),
                               dict(op='text',text='SHOULD NOT SEND'),
                               dict(op='release_all')])
        self.assertEqual(r['status'],'release_unverified')
        self.assertEqual(events,[])
        self.assertEqual(self.sends,[(17,True),(83,True),(83,False),(17,False),
                                     (17,False),(83,False)])
        self.assertEqual(b.held_keys,{'CTRL':17,'S':83})

    def test_unverified_button_up_aborts_remaining_ops(self):
        b,s=self.make();self.state=0;b.held_keys={}
        events=[]
        b.manifest=lambda:{'capabilities':{}}
        b.preflight=lambda program:None
        b.text=lambda value:events.append(('text',value))
        b._send=lambda item:self.sends.append(('mouse',))
        accepted=types.SimpleNamespace(accepted=True,error=None,required_capabilities=[])
        with patch.object(m,'admit_program',return_value=accepted):
            r=self.dispatch(s,[dict(op='pointer_button',button='left',down=True),
                               dict(op='pointer_button',button='left',down=False),
                               dict(op='text',text='SHOULD NOT SEND'),
                               dict(op='release_all')])
        self.assertEqual(r['status'],'release_unverified')
        self.assertEqual(events,[])
        self.assertEqual(self.sends,[('mouse',),('mouse',),('mouse',)])
        self.assertEqual(b.held_buttons,{'left'})

from runtime.backends.win32_v1 import session as m
if __name__=='__main__':unittest.main(verbosity=2)
