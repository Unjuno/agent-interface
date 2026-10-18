"""Owned-acquisition regressions; inert state only, never load graphics APIs."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from runtime.core_v1.contract import SCHEMA_PROGRAM
from .backend import BUTTONS, CGRect, CGPoint, CGSize, QuartzBackend, QuartzExecutionError
from .session import QuartzRuntimeSession


class VirtualInput:
    def __init__(self):
        self.keys=set(); self.buttons=set(); self.posts=[]; self.fault=None
        self.fail_up=False; self.fail_probe=False; self.null_event=False
        self.error=RuntimeError('first acquiring fault')
    def CGMainDisplayID(self): return 1
    def CGDisplayBounds(self, display): return CGRect(CGPoint(0,0),CGSize(100,100))
    def CGEventCreateKeyboardEvent(self, source, code, down):
        return None if self.null_event else ('key',code,down)
    def CGEventCreateMouseEvent(self, source, kind, point, number):
        down=next(kind==row[1] for row in BUTTONS.values() if row[0]==number)
        return ('button',number,down)
    def CGEventCreate(self, source): return ('position',)
    def CGEventGetLocation(self, event): return CGPoint(10,20)
    def CGEventPost(self, tap, event):
        kind,target,down=event
        self.posts.append(event)
        if down and self.fault=='before': raise self.error
        state=self.keys if kind=='key' else self.buttons
        if down: state.add(target)
        elif not self.fail_up: state.discard(target)
        if down and self.fault=='partial': raise self.error
    def CFRelease(self, event):
        if len(event)==3 and event[2] and self.fault=='dispose': raise self.error
    def CGEventSourceKeyState(self, source, code):
        if self.fail_probe: raise RuntimeError('readback unknown')
        return code in self.keys
    def CGEventSourceButtonState(self, source, number):
        if self.fail_probe: raise RuntimeError('readback unknown')
        return number in self.buttons


class AcquisitionTrackingTests(unittest.TestCase):
    def setUp(self):
        cdll=patch('runtime.backends.quartz_v1.backend.ctypes.CDLL',side_effect=AssertionError('native forbidden'))
        cdll.start();self.addCleanup(cdll.stop)
        sleeper=patch('runtime.backends.quartz_v1.backend.time.sleep');sleeper.start();self.addCleanup(sleeper.stop)
        self.v=VirtualInput(); self.b=object.__new__(QuartzBackend)
        self.b.cg=self.v;self.b.cf=SimpleNamespace(CFRelease=self.v.CFRelease)
        self.b.held_keys={};self.b.held_buttons=set();self.b.emissions=0
        self.b.accessibility_granted=True;self.b.screen_recording_granted=True
        self.s=QuartzRuntimeSession(self.b)
    def program(self, op, seq=7, binding=3):
        return {'schema':SCHEMA_PROGRAM,'program_id':'ordinary-acquisition-'+str(seq),
                'source':{'observation_seq':seq,'binding_revision':binding},
                'authority':{'lease_id':'inert-only','expires_at_ns':2000000},
                'terminal':{'release_all_required':True},
                'ops':[op,{'op':'key_state','key':'SHIFT','down':True},{'op':'release_all'}]}
    def dispatch(self, op, seq=7, binding=3):
        return self.s.dispatch(self.program(op,seq,binding),current_observation_seq=seq,current_binding_revision=binding,now_ns=1000000)
    def acquiring(self, kind):
        return {'op':'key_state','key':'A','down':True} if kind=='key' else {'op':'pointer_button','button':'left','down':True}
    def assert_fault_cleanup(self, kind, fault, sticky=False, unknown=False):
        self.v.fault=fault;self.v.fail_up=sticky;self.v.fail_probe=unknown
        row=self.dispatch(self.acquiring(kind))
        self.assertEqual(row['status'],'execution_failed')
        self.assertEqual(row['execution']['failed_op'],0)
        self.assertEqual(row['execution']['completed_ops'],[])
        self.assertEqual(row['execution']['error'],repr(self.v.error))
        self.assertNotIn(('key',56,True),self.v.posts) # failed-program tail
        self.assertIn((kind,0,False),self.v.posts) # genuine cleanup, not empty receipt
        release=row['execution']['releases'][0]
        if sticky or unknown:
            self.assertFalse(release['verified']);self.assertTrue(row['recovery_required'])
            before=list(self.v.posts)
            fresh=self.dispatch({'op':'key_state','key':'CTRL','down':True},8,4)
            self.assertEqual(fresh['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(self.v.posts,before)
            if unknown:self.assertTrue(self.b.held_keys if kind=='key' else self.b.held_buttons)
        else:
            self.assertTrue(release['verified']);self.assertFalse(row['recovery_required'])
            self.assertEqual((self.v.keys,self.v.buttons),(set(),set()))
            self.v.fault=None
            fresh=self.dispatch({'op':'key_state','key':'CTRL','down':True},8,4)
            self.assertEqual(fresh['status'],'completed')
            self.assertEqual((self.v.keys,self.v.buttons),(set(),set()))
    def test_key_disposal_error_releases_owned_acquisition(self):self.assert_fault_cleanup('key','dispose')
    def test_button_disposal_error_releases_owned_acquisition(self):self.assert_fault_cleanup('button','dispose')
    def test_key_partial_post_exception_releases_owned_acquisition(self):self.assert_fault_cleanup('key','partial')
    def test_button_partial_post_exception_releases_owned_acquisition(self):self.assert_fault_cleanup('button','partial')
    def test_key_sticky_cleanup_quarantines_fresh_request(self):self.assert_fault_cleanup('key','dispose',sticky=True)
    def test_button_sticky_cleanup_quarantines_fresh_request(self):self.assert_fault_cleanup('button','partial',sticky=True)
    def test_key_unknown_readback_retains_tracking_and_quarantine(self):self.assert_fault_cleanup('key','dispose',unknown=True)
    def test_button_unknown_readback_retains_tracking_and_quarantine(self):self.assert_fault_cleanup('button','partial',unknown=True)
    def test_error_before_input_is_cleaned_and_fresh_request_allowed(self):self.assert_fault_cleanup('key','before')
    def test_creation_null_does_not_invent_acquisition(self):
        self.v.null_event=True;row=self.dispatch(self.acquiring('key'))
        self.assertEqual(row['status'],'execution_failed');self.assertEqual(self.v.posts,[])
        self.assertEqual(self.b.held_keys,{});self.assertFalse(row['recovery_required'])
        self.v.null_event=False
        self.assertEqual(self.dispatch(self.acquiring('key'),8,4)['status'],'completed')
    def test_original_post_exception_identity_is_preserved(self):
        self.v.fault='partial'
        with self.assertRaises(QuartzExecutionError) as caught:self.b.execute(self.program(self.acquiring('key')))
        self.assertIs(caught.exception.__cause__,self.v.error)
        self.assertEqual((self.v.keys,self.v.buttons),(set(),set()))
    def test_healthy_program_completes_and_releases_all(self):
        row=self.dispatch(self.acquiring('button'))
        self.assertEqual(row['status'],'completed');self.assertEqual(row['execution']['completed_ops'],[0,1,2])
        self.assertEqual((self.v.keys,self.v.buttons),(set(),set()))

if __name__=='__main__':unittest.main()
