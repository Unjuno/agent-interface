"""Finite baseline admission/effect/stop controls; no display or model."""
import hashlib, importlib.util, time, unittest, sys
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]))
spec=importlib.util.spec_from_file_location('methods',HERE/'methods.py'); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class Bridge:
    def __init__(self,changed=False,release=True):
        self.phase=0; self.changed=changed; self.release=release; self.sequence=0; self.history={}; self.scope='private'; self.binding_revision=0
        self.active=None; self.review_required=False; self.session=SimpleNamespace(recovery_required=False)
        self.backend=SimpleNamespace(targets={'app':SimpleNamespace(id=20)}); self.target='app'; self.calls=[]; self.saved=[]
        self.store=SimpleNamespace(resolve_point=lambda *a,**k:{'eligible':True,'status':'VALID','valid_until_ns':time.monotonic_ns()+1_500_000_000})
    def _save(self,n,v): self.saved.append((n,v))
    def _focus_within_target(self): return True
    def observe(self):
        self.sequence+=1; rgb=Image.new('RGB',(640,480),'white'); d=ImageDraw.Draw(rgb); d.rectangle((0,0,20,20),fill='black')
        d.rectangle((40,152,160,205),fill=[(80,100,180),(40,180,60),(30,110,60)][self.phase])
        d.rectangle((290,152,430,205),outline='black',fill='red' if self.changed and self.phase else 'white')
        native={'sequence':self.sequence,'capture_ns':time.monotonic_ns(),'binding_revision':0,'pointer_binding':{'surface':20},'native':{'artifact':{'path':'fake.png','sha256':hashlib.sha256(rgb.tobytes()).hexdigest()}}}
        self.history[self.sequence]=(native,rgb); return native
    def click(self,alias,offset,**kwargs):
        self.calls.append((alias,kwargs)); self.phase+=1
        result={'status':'completed','recovery_required':False,'execution':{'releases':[{'verified':self.release,'keys_down':[],'buttons_down':[]}]}}
        self._save('result-'+str(len(self.calls)),result); return result
    def refs(self):
        self.observe(); rgb=self.history[1][1]
        return {alias:{'offset':[12,12],'box':box,'pixels':rgb.crop(box).tobytes()} for alias,box in [('field',(0,0,24,24)),('save',(280,148,304,172))]}
class Tests(unittest.TestCase):
    def test_positive_both_conditionally_complete_with_same_inputs(self):
        programs=[]
        for route in ('form','compiled'):
            b=Bridge(); r=module.run(b,b.refs(),'token',route)
            self.assertEqual((r['outcome'],r['completed_inputs']),('TASK_SUCCEEDED',2)); self.assertEqual(r['local_observations'],3)
            self.assertTrue(r['release_verified']); programs.append([(a,c['tail']) for a,c in b.calls])
        self.assertEqual(programs[0],programs[1])
    def test_changed_control_blocks_save_in_both_routes(self):
        for route in ('form','compiled'):
            b=Bridge(changed=True); r=module.run(b,b.refs(),'token',route)
            self.assertEqual((r['outcome'],r['reason'],r['completed_inputs']),('SAFE_YIELD','unknown_state',1)); self.assertEqual([a for a,k in b.calls],['field'])
    def test_release_failure_cannot_run_save(self):
        for route in ('form','compiled'):
            b=Bridge(release=False); r=module.run(b,b.refs(),'token',route)
            self.assertEqual(r['outcome'],'RUNTIME_FAILED'); self.assertEqual([a for a,k in b.calls],['field']); self.assertFalse(r['release_verified'])
if __name__=='__main__':unittest.main()
