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

if __name__=='__main__': unittest.main()
