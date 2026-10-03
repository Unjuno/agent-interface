"""Actual backend/session connection with inert SendInput/state endpoints."""
import json,unittest
from unittest.mock import patch
from . import backend as native
from .session import Win32RuntimeSession
from .inert_input import InputState
from .test_session_recovery import Endpoint
from runtime.core_v1.contract import SCHEMA_PROGRAM

class ActualBackendRecoveryTests(unittest.TestCase):
 def setUp(self):
  self.enterContext(patch.object(native.Win32Backend,'__init__',side_effect=AssertionError('constructor forbidden')))
  self.enterContext(patch.object(native.ctypes,'WinDLL',create=True,side_effect=AssertionError('WinDLL forbidden')))
  self.enterContext(patch.object(native.time,'sleep',return_value=None))
  self.enterContext(patch.object(native.time,'monotonic_ns',return_value=1))
  self.b=native.Win32Backend.__new__(native.Win32Backend);self.b.held_keys={};self.b.held_buttons=set();self.b.emissions=0;self.b.user32=InputState(stubborn=True);self.s=Win32RuntimeSession(self.b)
 def dispatch(self):
  p={'schema':SCHEMA_PROGRAM,'program_id':'actual-coupling','source':{'observation_seq':7,'binding_revision':3},'authority':{'lease_id':'ordinary-coupling','expires_at_ns':100},'terminal':{'release_all_required':True},'ops':[{'op':'key_state','key':'Q','down':True},{'op':'release_all'}]}
  r=self.s.dispatch(p,current_observation_seq=7,current_binding_revision=3,now_ns=1);print(json.dumps({'test':self.id(),'reply':r,'events':self.b.user32.events,'held_keys':self.b.held_keys,'inert_down':sorted(self.b.user32.down),'emissions':self.b.emissions}));return r
 def test_actual_backend_unverified_release_blocks_later_input(self):
  self.assertEqual(self.dispatch()['status'],'release_unverified');self.assertEqual(self.b.held_keys,{'Q':81});events=list(self.b.user32.events);r=self.dispatch();self.assertEqual(r['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(self.b.user32.events,events)
 def test_actual_backend_recovery_retains_then_retires_obligation_without_replay(self):
  self.assertEqual(self.dispatch()['status'],'release_unverified');f=getattr(self.s,'recover_input',None);self.assertTrue(callable(f),'explicit recovery missing');first=f();print(json.dumps({'test':self.id(),'recovery':first,'events':self.b.user32.events}));self.assertEqual(first['status'],'recovery_failed');self.assertEqual(self.b.held_keys,{'Q':81});self.b.user32.stubborn=False;events=len(self.b.user32.events);last=f();print(json.dumps({'test':self.id(),'recovery':last,'events':self.b.user32.events}));self.assertEqual(last['status'],'input_recovered');self.assertEqual(self.b.held_keys,{});self.assertEqual(self.b.user32.down,set());self.assertEqual(self.b.user32.events[events:],[{'send':81,'down':False},{'query':81}]);self.assertEqual(self.dispatch()['status'],'completed')

if __name__=='__main__':unittest.main()
