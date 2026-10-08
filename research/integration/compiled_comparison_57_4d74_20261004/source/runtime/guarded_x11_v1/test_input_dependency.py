"""Opt-in dependency checks through the real bridge; inert capture/emission only."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PIL import Image
from runtime.guarded_x11_v1.bridge import NativeHandleBridge, _GuardedBackend
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError, X11ExecutionError

TAIL = [{'op':'key_chord','keys':['CTRL','s']}]

class InputDependencyTests(unittest.TestCase):
    def setUp(self):
        self.b = object.__new__(NativeHandleBridge)
        b=self.b;b.active=None;b.review_required=False;b.session=SimpleNamespace(recovery_required=False)
        b.scope='guard:test';b.binding_revision=2;b.sequence=0;b.history={};b.checks=[];b.additional_checks=[]
        b.deadline=100;b._binding=Mock(return_value={'focus':4});b._focus_within_target=Mock(return_value=True)
        b.store=SimpleNamespace(resolve_point=Mock(return_value={'eligible':True,'point':[10,20]}))
        b.observe=self.capture;b._save=Mock();b.target='app'
        self.clock=1
        patcher=patch('time.monotonic_ns',side_effect=lambda:self.clock);patcher.start();self.addCleanup(patcher.stop)

    def capture(self):
        b=self.b;b.sequence+=1
        source={'sequence':b.sequence,'pointer_binding':{'focus':4},'binding_revision':2}
        b.history[b.sequence]=(source,Image.new('RGB',(2,2),'white'))
        return source

    def activate(self):self.b.active=('save',[0,0])

    def test_existing_check_precedes_callback_and_source_is_defensive(self):
        def verify(stage,source,image):
            self.b.store.resolve_point.assert_called_once()
            self.assertEqual(source['sequence'],1);self.assertEqual(stage,'before_admission')
            source['pointer_binding']['focus']=99;image.putpixel((0,0),(0,0,0))
            return True
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=verify):
            self.activate();out=self.b.check('before_admission')
        self.assertEqual(out['point'],[10,20]);self.assertEqual(self.b.history[1][0]['pointer_binding']['focus'],4)
        self.assertEqual(self.b.history[1][1].getpixel((0,0)),(255,255,255))
        self.assertTrue(self.b.additional_checks[0]['eligible'])

    def test_existing_refusal_never_calls_additional_check(self):
        verify=Mock(return_value=True);self.b.store.resolve_point.return_value={'eligible':False,'status':'stale'}
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=verify):
            self.activate()
            with self.assertRaises(X11BackendError):self.b.check('before_admission')
        verify.assert_not_called()

    def test_false_none_or_truthy_non_boolean_refuses(self):
        for value in [False,None,1,'yes']:
            with self.subTest(value=value):
                self.b.active=None
                with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:value):
                    self.activate()
                    with self.assertRaises(X11BackendError):self.b.check('before_admission')
                self.assertFalse(self.b.additional_checks[-1]['eligible'])

    def test_source_freshness_consumed_by_callback_refuses_without_recapture(self):
        self.b.store.resolve_point.side_effect=[{'eligible':True,'point':[10,20]},
                                               {'eligible':False,'status':'expired'}]
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:True):
            self.activate()
            with self.assertRaisesRegex(X11BackendError,'expired during additional check'):
                self.b.check('before_admission')
        self.assertEqual(self.b.sequence,1)
        self.assertFalse(self.b.additional_checks[-1]['eligible'])

    def test_callback_exception_retains_refusal(self):
        def verify(*args):raise OSError('unavailable')
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=verify):
            self.activate()
            with self.assertRaisesRegex(X11BackendError,'unavailable'):self.b.check('before_admission')
        self.assertFalse(self.b.additional_checks[-1]['eligible'])

    def test_deadline_focus_and_source_changes_during_callback_refuse(self):
        for change in ['deadline','focus','sequence','scope','revision','review','recovery','extended_lease','active','registration']:
            self.b.active=None;self.b.scope='guard:test';self.b.binding_revision=2
            self.b.sequence=0;self.b.history={};self.b.review_required=False
            self.b.session.recovery_required=False;self.b._binding.return_value={'focus':4}
            self.clock=1;self.b.deadline=100
            def verify(*args):
                if change=='deadline':self.clock=100
                elif change=='focus':self.b._binding.return_value={'focus':99}
                elif change=='sequence':self.b.sequence+=1
                elif change=='scope':self.b.scope='changed'
                elif change=='revision':self.b.binding_revision+=1
                elif change=='review':self.b.review_required=True
                elif change=='extended_lease':self.b.deadline=200
                elif change=='active':self.b.active=('other',[0,0])
                elif change=='registration':self.b._input_guard=None
                else:self.b.session.recovery_required=True
                return True
            with self.subTest(change=change),self.b.input_guard('save',[0,0],tail=TAIL,verify=verify):
                self.activate()
                with self.assertRaises(X11BackendError):self.b.check('before_admission')

    def test_no_guard_keeps_one_capture_and_no_extra_check(self):
        self.activate();self.b.check('before_admission');self.assertEqual(self.b.sequence,1)
        self.assertEqual(self.b.additional_checks,[])

    def test_other_alias_keeps_existing_check_without_callback(self):
        verify=Mock(return_value=True)
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=verify):
            self.b.active=('entry',[0,0]);self.b.check('before_admission')
        verify.assert_not_called()

    def test_nested_registration_and_registration_during_input_refuse(self):
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:True):
            with self.assertRaises(RuntimeError):
                with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:True):pass
        self.activate()
        with self.assertRaises(RuntimeError):
            with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:True):pass

    def test_context_restores_after_exception(self):
        with self.assertRaises(OSError):
            with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:True):raise OSError('caller')
        self.assertIsNone(self.b._input_guard)

    def test_changed_tail_offset_or_interaction_refuses_before_input(self):
        for alias,offset,tail,interaction in [('save',[1,0],TAIL,'keyboard'),('save',[0,0],[{'op':'text','text':'x'}],'keyboard'),('save',[0,0],TAIL,'click')]:
            with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:True):
                with self.assertRaises(ValueError):self.b._run_guarded(alias,offset,tail=tail,interaction=interaction)
            self.b._save.assert_not_called();self.assertEqual(self.b.sequence,0)

    def test_rebinding_before_capture_refuses(self):
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=lambda *a:True):
            self.b.binding_revision=3
            with self.assertRaises(X11BackendError):self.b.keyboard('save',[0,0],tail=TAIL)
        self.assertEqual(self.b.sequence,0)

    def test_refusal_after_modifier_preserves_prefix_and_release(self):
        backend=object.__new__(_GuardedBackend);backend.owner=self.b;backend.emissions=0
        backend.preflight=Mock();backend._refresh_keyboard_mapping=Mock(return_value=False)
        held=[];emitted=[]
        def emit(key,down):
            emitted.append((key,down));backend.emissions+=1
            if down:held.append(key)
            elif key in held:held.remove(key)
        def release():
            for key in list(held):backend.key_state(key,False)
            return {'verified':True,'keys_down':held.copy(),'buttons_down':[]}
        backend.release_all=release;checks=[]
        def verify(stage,*args):checks.append(stage);return len(checks)==1
        with self.b.input_guard('save',[0,0],tail=TAIL,verify=verify),patch.object(X11Backend,'key_state',side_effect=emit):
            self.activate()
            with self.assertRaises(X11ExecutionError) as caught:backend.execute({'ops':TAIL})
        self.assertEqual(emitted,[('CTRL',True),('CTRL',False)])
        self.assertEqual(checks,['before_key_press:CTRL','before_key_press:s'])
        self.assertTrue(caught.exception.execution['releases'][0]['verified'])
        self.assertEqual(caught.exception.execution['program_emissions'],2)

if __name__=='__main__':unittest.main()
