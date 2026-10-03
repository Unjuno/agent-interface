"""Ordinary session/core recovery tests; all backend effect endpoints inert."""
import copy,json,unittest
from unittest.mock import patch
from runtime.backends.win32_v1 import backend as native
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM

NEUTRAL={'verified':True,'keys_down':[],'buttons_down':[]}
class Endpoint(native.Win32Backend):
    def __init__(self):
        self.emissions=0;self.calls=[];self.reply={'releases':[copy.deepcopy(NEUTRAL)]};self.pre_error=None;self.execute_error=None;self.cleanup=copy.deepcopy(NEUTRAL)
    def manifest(self):self.calls.append('manifest');return super().manifest()
    def preflight(self,p):
        self.calls.append('preflight')
        if self.pre_error:raise self.pre_error
    def execute(self,p):
        self.calls.append('execute');self.emissions+=1
        if self.execute_error:raise self.execute_error
        return copy.deepcopy(self.reply)
    def release_all(self):
        self.calls.append('release')
        if isinstance(self.cleanup,Exception):raise self.cleanup
        return copy.deepcopy(self.cleanup)

class SessionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(native.Win32Backend,'__init__',side_effect=AssertionError('native constructor forbidden')))
        self.enterContext(patch.object(native.ctypes,'WinDLL',create=True,side_effect=AssertionError('WinDLL forbidden')))
        self.b=Endpoint();self.s=Win32RuntimeSession(self.b)
    def dispatch(self,revision=3,seq=7):
        p={'schema':SCHEMA_PROGRAM,'program_id':'recovery-regression','source':{'observation_seq':seq,'binding_revision':revision},'authority':{'lease_id':'ordinary-recovery','expires_at_ns':100},'terminal':{'release_all_required':True},'ops':[{'op':'key_state','key':'Q','down':True},{'op':'release_all'}]}
        try:r=self.s.dispatch(p,current_observation_seq=7,current_binding_revision=revision,now_ns=1)
        except Exception as e:
            print(json.dumps({'test':self.id(),'raised':type(e).__name__,'calls':self.b.calls,'emissions':self.b.emissions}));raise
        print(json.dumps({'test':self.id(),'reply':r,'calls':self.b.calls,'emissions':self.b.emissions}));return r
    def gated(self,revision=3):
        before=list(self.b.calls);count=self.b.emissions;r=self.dispatch(revision)
        self.assertEqual(r['status'],'refused');self.assertEqual(r['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(self.b.calls,before);self.assertEqual(self.b.emissions,count)
    def recover(self):
        f=getattr(self.s,'recover_input',None);self.assertTrue(callable(f),'missing explicit recovery endpoint')
        r=f();print(json.dumps({'test':self.id(),'recovery':r,'calls':self.b.calls,'emissions':self.b.emissions}));return r
    def uncertain(self):
        self.b.reply={'releases':[{'verified':False,'keys_down':['Q'],'buttons_down':[]}]};self.assertEqual(self.dispatch()['status'],'release_unverified')
    def test_healthy_repeated_dispatch_remains_available(self):
        self.assertEqual(self.dispatch()['status'],'completed');self.assertEqual(self.dispatch()['status'],'completed');self.assertEqual(self.b.emissions,2)
    def test_unverified_release_stops_before_backend_access(self):self.uncertain();self.gated()
    def test_missing_release_stops_before_backend_access(self):self.b.reply={'releases':[]};self.assertEqual(self.dispatch()['status'],'release_unverified');self.gated()
    def test_malformed_or_nonempty_release_never_completes(self):
        bad=[None,{},[{'verified':1,'keys_down':[],'buttons_down':[]}],[{'verified':'yes','keys_down':[],'buttons_down':[]}],[{'verified':True,'keys_down':['Q'],'buttons_down':[]}],[{'verified':True,'keys_down':[],'buttons_down':['left']}],[{'verified':True,'keys_down':[]}],[{'verified':True,'keys_down':[],'buttons_down':None}],[None],(NEUTRAL,)]
        for releases in bad:
            with self.subTest(releases=releases):
                self.b=Endpoint();self.s=Win32RuntimeSession(self.b);self.b.reply={'releases':releases};self.assertEqual(self.dispatch()['status'],'release_unverified');self.gated()
    def test_backend_execution_error_requires_recovery(self):
        self.b.execute_error=native.Win32BackendError('inert failure');self.assertEqual(self.dispatch()['status'],'execution_failed');self.gated()
    def test_unexpected_execution_error_remains_original_exception_and_gated(self):
        self.b.execute_error=RuntimeError('inert uncertain failure')
        with self.assertRaisesRegex(RuntimeError,'inert uncertain'):self.dispatch()
        self.gated()
    def test_preflight_unverified_cleanup_requires_recovery(self):
        self.b.pre_error=native.Win32BackendError('inert pre-input refusal');self.b.cleanup={'verified':False,'keys_down':['Q'],'buttons_down':[]};self.assertEqual(self.dispatch()['error'],'BACKEND_CONSTRAINT');self.gated()
    def test_preflight_cleanup_exception_requires_recovery(self):
        self.b.pre_error=native.Win32BackendError('inert pre-input refusal');self.b.cleanup=RuntimeError('inert cleanup unavailable')
        with self.assertRaisesRegex(RuntimeError,'cleanup unavailable'):self.dispatch()
        self.gated()
    def test_verified_preflight_cleanup_does_not_disable_healthy_session(self):
        self.b.pre_error=native.Win32BackendError('inert refusal');self.assertEqual(self.dispatch()['status'],'refused');self.b.pre_error=None;self.assertEqual(self.dispatch()['status'],'completed')
    def test_binding_change_does_not_clear_uncertainty(self):self.uncertain();self.gated(revision=4)
    def test_direct_cleanup_does_not_clear_session_gate(self):
        self.uncertain();self.assertEqual(self.b.release_all(),NEUTRAL);self.gated()
    def test_recovery_not_required_does_not_call_backend(self):
        r=self.recover();self.assertEqual(r['error'],'INPUT_RECOVERY_NOT_REQUIRED');self.assertIs(r['release_attempted'],False);self.assertEqual(self.b.calls,[])
    def test_explicit_recovery_neutralizes_once_without_replay(self):
        self.uncertain();before=list(self.b.calls);emissions=self.b.emissions;r=self.recover();self.assertEqual(r['status'],'input_recovered');self.assertIs(r['replay_allowed'],False);self.assertIsNone(r['task_success']);self.assertEqual(self.b.calls,before+['release']);self.assertEqual(self.b.emissions,emissions)
        self.b.reply={'releases':[copy.deepcopy(NEUTRAL)]};self.assertEqual(self.dispatch()['status'],'completed');self.assertEqual(self.b.emissions,emissions+1)
    def test_failed_recovery_stays_gated_until_explicit_reported_neutral(self):
        self.uncertain()
        for cleanup in [RuntimeError('inert cleanup failure'),{'verified':False,'keys_down':['Q'],'buttons_down':[]},{'verified':1,'keys_down':[],'buttons_down':[]}]:
            self.b.cleanup=cleanup;before=len(self.b.calls);r=self.recover();self.assertEqual(r['status'],'recovery_failed');self.assertEqual(self.b.calls[before:],['release']);self.gated()
        self.b.cleanup=copy.deepcopy(NEUTRAL);self.assertEqual(self.recover()['status'],'input_recovered')
    def test_core_refusal_keeps_no_input_and_later_valid_admission(self):
        self.assertEqual(self.dispatch(seq=6)['error'],'STALE_OBSERVATION');self.assertEqual(self.b.emissions,0);self.assertEqual(self.dispatch()['status'],'completed')
    def test_non_mapping_execution_result_is_uncertain_and_gated(self):
        self.b.reply=None;self.assertEqual(self.dispatch()['status'],'release_unverified');self.gated()

if __name__=='__main__':unittest.main()
