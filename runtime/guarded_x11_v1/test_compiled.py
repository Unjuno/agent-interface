"""Shared X11 adapter boundaries; fake captures/input, no display or model."""
import copy
import hashlib
import time
from types import SimpleNamespace
from unittest.mock import Mock
import unittest
from PIL import Image
from runtime.core_v1.test_compiled_gui import interface
from runtime.guarded_x11_v1.compiled import run, _Adapter

class Bridge:
    def __init__(self):
        self.scope='private'; self.binding_revision=0; self.sequence=0
        self.active=None; self.review_required=False
        self.session=SimpleNamespace(recovery_required=False)
        self.backend=SimpleNamespace(targets={'app':SimpleNamespace(id=20)})
        self.target='app'; self.history={}; self.saved=[]; self.inputs=[]
        self.store=SimpleNamespace(resolve_point=Mock(side_effect=self.resolve))
        self.phase=0; self.release=True
    def _save(self,name,value): self.saved.append((name,copy.deepcopy(value)))
    def _focus_within_target(self): return True
    def resolve(self,*args,**kwargs):
        return {'eligible':True,'status':'VALID','valid_until_ns':time.monotonic_ns()+1_500_000_000}
    def observe(self):
        self.sequence+=1
        image=Image.new('RGB',(32,32),(self.phase,20,30))
        observation={'sequence':self.sequence,'capture_ns':time.monotonic_ns(),
            'binding_revision':0,'pointer_binding':{'surface':20},
            'native':{'artifact':{'sha256':hashlib.sha256(image.tobytes()).hexdigest()}}}
        self.history[self.sequence]=(observation,image)
        return observation
    def click(self,alias,offset,**kwargs):
        self.inputs.append((alias,offset,copy.deepcopy(kwargs))); self.phase+=1
        return {'status':'completed','execution':{'releases':[{'verified':self.release,'keys_down':[],'buttons_down':[]}]}}
    keyboard=click; move=click

def spec():
    s=interface(); s['surface']='x11-window-20'; s['predicates'].append('present')
    s['symbols']['field'].update(identity_predicate='present',dependencies=['present'])
    s['method']['max_runtime_ms']=1000
    return s

def bindings():
    return {a:{'interaction':'click','offset':[2,2],'tail':[]} for a in ('enter','save')}

def perceive(native,image): return {'phase':image.getpixel((0,0))[0],'present':True}
def verify(payload,native,image): return {'status':'succeeded','evidence_ref':payload['observation']['evidence_ref']}

class CompiledX11Tests(unittest.TestCase):

    def test_top_level_native_release_is_retained_on_pre_execution_refusal(self):
        b=Bridge()
        b.click=lambda *a,**k:{'status':'refused','error':'BACKEND_CONSTRAINT',
          'program_execution_started':False,'program_emissions':0,'backend_emissions':0,
          'release':{'verified':True,'keys_down':[],'buttons_down':[]},'recovery_required':False}
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','execution_failed'))
        terminal=next(row for name,row in b.saved if name.endswith('-terminal.json'))
        self.assertEqual(terminal['release'],{'verified':True,'keys_down':[],'buttons_down':[]})
        self.assertNotIn('input_dispatched',terminal)
        self.assertEqual(r['completed_transitions'],0)
    def test_no_input_flag_cannot_hide_top_level_unverified_or_held_release(self):
        for release in ({'verified':False,'keys_down':[],'buttons_down':[]},
                        {'verified':False,'keys_down':['CTRL'],'buttons_down':[]},
                        {'verified':True,'keys_down':[],'buttons_down':['left']}):
            with self.subTest(release=release):
                b=Bridge();b.click=lambda *a,**k:{'status':'refused','input_dispatched':False,'release':release}
                r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
                self.assertEqual(r['outcome'],'RUNTIME_FAILED')
                terminal=next(row for name,row in b.saved if name.endswith('-terminal.json'))
                self.assertNotIn('input_dispatched',terminal)
                self.assertEqual(terminal['release']['keys_down'],release['keys_down'])
                self.assertEqual(terminal['release']['buttons_down'],release['buttons_down'])
    def test_conflicting_native_release_receipts_do_not_certify_neutrality(self):
        b=Bridge()
        b.click=lambda *a,**k:{'status':'completed',
          'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]},
          'release':{'verified':False,'keys_down':['CTRL'],'buttons_down':[]}}
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['outcome'],'RUNTIME_FAILED')
        terminal=next(row for name,row in b.saved if name.endswith('-terminal.json'))
        self.assertEqual(terminal['release']['keys_down'],['CTRL'])
    def test_session_recovery_prevents_success_despite_top_level_neutral_release(self):
        b=Bridge()
        def recovery(*a,**k):
            b.session.recovery_required=True
            return {'status':'completed','release':{'verified':True,'keys_down':[],'buttons_down':[]}}
        b.click=recovery;r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['outcome'],'RUNTIME_FAILED')
    def test_malformed_top_level_release_does_not_certify_abstention(self):
        for release in (None,{}, {'verified':True,'keys_down':None,'buttons_down':[]}):
            with self.subTest(release=release):
                b=Bridge();b.click=lambda *a,**k:{'status':'refused','input_dispatched':False,'release':release}
                r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
                self.assertEqual(r['outcome'],'RUNTIME_FAILED')

    def test_invalid_native_alias_fails_before_capture_or_callback(self):
        for alias in ('sheet-context','Sheet','a'*33,'x y'):
            with self.subTest(alias=alias):
                b=Bridge();s=spec();s['symbols']['field']['target_reference']=alias
                perception=Mock(side_effect=perceive);verifier=Mock(side_effect=verify)
                with self.assertRaisesRegex(ValueError,'target alias'):
                    run(b,s,bindings(),perceive=perception,verify_effect=verifier)
                self.assertEqual(b.sequence,0);self.assertEqual(b.inputs,[])
                perception.assert_not_called();verifier.assert_not_called()
    def test_valid_native_aliases_preserve_symbolic_name_flexibility(self):
        for alias in ('sheet_context','a'*32):
            with self.subTest(alias=alias):
                b=Bridge();s=spec();symbol=s['symbols'].pop('field')
                symbol['target_reference']=alias
                s['symbols']['symbol-with-hyphen']=symbol
                for action in s['actions'].values():action['target_symbol']='symbol-with-hyphen'
                r=run(b,s,bindings(),perceive=perceive,verify_effect=verify)
                self.assertEqual(r['outcome'],'TASK_SUCCEEDED')
    def test_boolean_phase_cannot_verify_integer_effect_or_dispatch_next_action(self):
        b=Bridge()
        def typed(native,image):
            values=perceive(native,image)
            if values['phase']==1:values['phase']=True
            return values
        verifier=Mock(side_effect=verify)
        r=run(b,spec(),bindings(),perceive=typed,verify_effect=verifier)
        self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','effect_failed'))
        self.assertEqual(r['completed_transitions'],1);self.assertEqual(r['pending_effect']['action'],'enter')
        self.assertEqual(len(b.inputs),1);verifier.assert_not_called()
        effects=[row for name,row in b.saved if name.endswith('-event.json') and row.get('event')=='effect_checked']
        self.assertEqual(effects[-1]['status'],'failed')

    def test_live_adapter_selects_second_action_from_new_pixels_and_clamps_deadline(self):
        b=Bridge(); before=time.monotonic_ns()
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['outcome'],'TASK_SUCCEEDED'); self.assertEqual(r['completed_transitions'],2)
        self.assertEqual([o['predicates']['phase'] for o in r['observations']],[0,1,2])
        self.assertEqual(len(b.inputs),2)
        self.assertTrue(all(before < c[2]['expires_at_ns'] <= r['started_ns']+1_000_000_000 for c in b.inputs))
        self.assertTrue(any('receipt' in name for name,row in b.saved))
    def test_unknown_pixels_never_send_input(self):
        b=Bridge(); r=run(b,spec(),bindings(),perceive=lambda n,i:{},verify_effect=verify)
        self.assertEqual(r['reason'],'unknown_state'); self.assertEqual(b.inputs,[])
    def test_false_identity_cannot_be_overridden_by_action_branch(self):
        b=Bridge(); r=run(b,spec(),bindings(),perceive=lambda n,i:{'phase':0,'present':False},verify_effect=verify)
        self.assertEqual(r['reason'],'missing_symbol'); self.assertEqual(b.inputs,[])
    def test_missing_reference_after_first_action_retains_prefix(self):
        b=Bridge(); original=b.resolve
        b.store.resolve_point.side_effect=lambda *a,**k: original(*a,**k) if b.phase==0 else {'eligible':False,'status':'MISSING'}
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['reason'],'missing_symbol'); self.assertEqual(r['completed_transitions'],1); self.assertEqual(len(b.inputs),1)
    def test_release_failure_prevents_following_input(self):
        b=Bridge(); b.release=False
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['outcome'],'RUNTIME_FAILED'); self.assertEqual(len(b.inputs),1)
    def test_perception_cannot_mutate_guard_pixels_or_source_metadata(self):
        b=Bridge()
        def mutate(n,i):
            v=perceive(n,i); n['sequence']=-1; i.paste('black',(0,0,32,32)); return v
        r=run(b,spec(),bindings(),perceive=mutate,verify_effect=verify)
        self.assertEqual(r['outcome'],'TASK_SUCCEEDED')
        self.assertEqual(b.history[1][0]['sequence'],1); self.assertEqual(b.history[1][1].getpixel((0,0)),(0,20,30))
    def test_scope_change_during_perception_cannot_send_input(self):
        b=Bridge()
        def changed(n,i): b.scope='changed'; return perceive(n,i)
        r=run(b,spec(),bindings(),perceive=changed,verify_effect=verify)
        self.assertEqual(r['reason'],'association_changed'); self.assertEqual(b.inputs,[])
    def test_scope_change_during_final_observation_cannot_claim_success(self):
        b=Bridge()
        def changed(n,i):
            if b.phase==2: b.scope='changed'
            return perceive(n,i)
        r=run(b,spec(),bindings(),perceive=changed,verify_effect=verify)
        self.assertEqual(r['reason'],'association_changed'); self.assertEqual(len(b.inputs),2)
    def test_scope_change_in_final_verifier_cannot_claim_success(self):
        b=Bridge()
        def changed(p,n,i):
            if b.phase==2: b.scope='changed'
            return verify(p,n,i)
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=changed)
        self.assertEqual(r['reason'],'effect_unavailable'); self.assertEqual(len(b.inputs),2)
    def test_callback_failure_retains_exception_without_input_or_retry(self):
        b=Bridge()
        def bad(n,i): raise RuntimeError('perception failed')
        with self.assertRaisesRegex(RuntimeError,'perception failed'):
            run(b,spec(),bindings(),perceive=bad,verify_effect=verify)
        self.assertEqual(b.inputs,[]); self.assertTrue(any('exception' in n for n,r in b.saved))
    def test_wrong_initial_surface_rejects_before_capture(self):
        b=Bridge(); s=spec(); s['surface']='other'
        with self.assertRaises(ValueError): run(b,s,bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(b.sequence,0)
    def test_authorization_is_one_use_and_bound_to_observed_sequence(self):
        b=Bridge(); a=_Adapter(b,spec(),bindings(),perceive,verify,lambda:False)
        o=a.observe({'state':'empty','required_predicates':spec()['predicates']})
        request={'interface_id':'test','session_scope':'private','action':'enter','operation':'enter','symbol':spec()['symbols']['field'],'observation':o}
        admission=a.admit(request)
        payload={'action':'enter','operation':'enter','authorization':admission['authorization'],'expected_sequence':o['sequence'],'valid_until_ns':admission['valid_until_ns']}
        self.assertEqual(a.execute(payload)['status'],'completed')
        self.assertNotEqual(a.execute(payload)['status'],'completed'); self.assertEqual(len(b.inputs),1)
    def test_method_bindings_are_copied_before_perception(self):
        b=Bridge(); bindings_value=bindings()
        def mutate(n,i): bindings_value['enter']['tail'].append({'op':'text','text':'unapproved'}); return perceive(n,i)
        run(b,spec(),bindings_value,perceive=mutate,verify_effect=verify)
        self.assertEqual(b.inputs[0][2]['tail'],[])

    def test_changed_binding_after_admission_is_no_input_safe_yield(self):
        from unittest.mock import patch
        b=Bridge(); original=_Adapter.admit
        def changed(adapter,request):
            result=original(adapter,request); b.binding_revision+=1; return result
        with patch.object(_Adapter,'admit',changed):
            r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','execution_refused'))
        self.assertEqual(b.inputs,[]);self.assertEqual(r['completed_transitions'],0)
        terminals=[row for name,row in b.saved if name.endswith('-terminal.json')]
        self.assertIs(terminals[0]['input_dispatched'],False)
        self.assertIs(terminals[0]['release']['verified'],False)
    def test_changed_binding_before_second_input_preserves_verified_prefix(self):
        from unittest.mock import patch
        b=Bridge();original=_Adapter.admit
        def changed(adapter,request):
            result=original(adapter,request)
            if b.phase==1:b.binding_revision+=1
            return result
        with patch.object(_Adapter,'admit',changed):
            r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','execution_refused'))
        self.assertEqual(len(b.inputs),1);self.assertEqual(r['completed_transitions'],1)
        self.assertEqual(r['transitions'][0]['action'],'enter')
    def test_native_guard_refusal_without_input_is_not_release_failure(self):
        b=Bridge();b.click=lambda *a,**k:{'status':'refused','input_dispatched':False,'error':'STALE'}
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['reason'],'execution_refused');self.assertEqual(b.inputs,[])
    def test_no_input_attestation_does_not_hide_native_release_failure(self):
        b=Bridge()
        b.click=lambda *a,**k:{'status':'refused','input_dispatched':False,
          'execution':{'releases':[{'verified':False,'keys_down':['CTRL'],'buttons_down':[]}]}}
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['outcome'],'RUNTIME_FAILED');self.assertEqual(b.inputs,[])
    def test_no_input_refusal_does_not_hide_recovery_required(self):
        b=Bridge()
        def refused(*a,**k):
            b.session.recovery_required=True
            return {'status':'refused','input_dispatched':False,'recovery_required':True}
        b.click=refused
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['outcome'],'RUNTIME_FAILED');self.assertEqual(b.inputs,[])
    def test_no_input_attestation_does_not_hide_execution_without_release(self):
        b=Bridge()
        b.click=lambda *a,**k:{'status':'refused','input_dispatched':False,
          'execution':{'program_emissions':1,'releases':[]}}
        r=run(b,spec(),bindings(),perceive=perceive,verify_effect=verify)
        self.assertEqual(r['outcome'],'RUNTIME_FAILED');self.assertEqual(b.inputs,[])
if __name__=='__main__': unittest.main()
