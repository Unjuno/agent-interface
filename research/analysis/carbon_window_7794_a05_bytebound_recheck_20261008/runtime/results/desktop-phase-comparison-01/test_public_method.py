import hashlib,importlib.util,json,tempfile,time,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
spec=importlib.util.spec_from_file_location('strong_public_calc',Path(__file__).with_name('public_method.py'))
method=importlib.util.module_from_spec(spec);spec.loader.exec_module(method)

class PublicCompositionTests(unittest.TestCase):
    def exercise(self,case='success',compact=False):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'run';programs=[];observations=[];readings=[]
            def capture(*args,**kw):
                n=len(observations)+1;path=root/f'image-{n}.png'
                Image.new('RGB',(1280,800),'white').save(path)
                digest=hashlib.sha256(path.read_bytes()).hexdigest();stamp=time.monotonic_ns()
                native={'sha256':'rgb-fixture','capture_started_ns':stamp,'capture_ended_ns':stamp,
                  'target':'app','native_window_id':123,'frame':'screen_physical_px','region':[0,0,1280,800],
                  'width':1280,'height':800,'artifact':{'mime_type':'image/png','path':str(path),'sha256':digest,'source_raw_sha256':'rgb-fixture'}}
                observations.append(native)
                return {'schema':'agent-interface/runtime-observation-v1','status':'returned','observation_id':str(n),'input_dispatched':False,'side_effect_authority':False,'observation':native}
            def dispatch(session,program,**kw):
                programs.append(program)
                if case=='uncertain':raise OSError('uncertain delivery')
                stamp=time.monotonic_ns()
                return {'schema':'agent-interface/runtime-dispatch-result-v1','status':'returned','result':{'status':'completed','recovery_required':False,'execution':{'ended_ns':stamp,'releases':[{'verified':case!='release_failure','keys_down':[],'buttons_down':[],'monotonic_ns':stamp}],'observations':[]}}}
            def inspect_after(*a,**k):
                raw=capture()
                return {'status':'needs_review','input_dispatched':False,'authority_granted':False,
                  'error':'TARGET_CHANGED_DURING_CAPTURE' if case=='withheld' else None,
                  'review_request':{'tool':'interface_review_target'},'observation_report':raw}
            owner=SimpleNamespace(binding_revision=1,targets={'app':123},family_roots={'app':123},dispatch_attempted=False,get=lambda:SimpleNamespace(backend=object()),inspect_after_dispatch=inspect_after)
            def read(rgb,regions,out):
                readings.append(rgb.size)
                return {'A1':{'value':None if case=='unknown' and len(readings)==2 else '317'},'A2':{'value':'529'}}
            with patch.object(method,'observe_in_session',side_effect=capture),patch.object(method,'dispatch_in_session',side_effect=dispatch),patch.object(method,'inspect_focused_target',return_value={'window_id':124 if case=='changed' else 123}):
                result=method.run(owner,{'box':[0,0,2,2],'pixels':b'\xff'*12},{'A1':[1,1,2,2],'A2':[2,2,3,3]},root,read,sequence=1,compact=compact)
            return result,programs,readings,[(p.name,json.loads(p.read_text())) for p in root.glob('*-input.json')]
    def test_public_batch_continues_to_save_without_model_or_graph(self):
        for compact in [False,True]:
            result,programs,reads,raw=self.exercise(compact=compact)
            self.assertEqual(result['confirmed_completed_inputs'],['enter','save'])
            self.assertEqual(result['reason'],'save_handoff_requires_primary_review')
            self.assertIsNone(result['task_success']);self.assertFalse(result['replay_allowed'])
            self.assertEqual(len(programs),2);self.assertEqual(len(reads),2);self.assertEqual(len(raw),2)
            self.assertEqual(programs[0]['ops'][1:-1],method.ENTER)
            self.assertEqual(programs[1]['ops'][1:-1],method.SAVE)
    def test_unknown_and_changed_dependency_stop_before_save(self):
        for case,count,prefix in [('unknown',1,['enter']),('changed',0,[])]:
            result,programs,*_=self.exercise(case)
            self.assertEqual(len(programs),count);self.assertEqual(result['confirmed_completed_inputs'],prefix)
            self.assertEqual(result['outcome'],'SAFE_YIELD')
    def test_release_failure_uncertain_input_and_withheld_image_do_not_continue(self):
        for case,prefix in [('release_failure',[]),('uncertain',[]),('withheld',['enter'])]:
            result,programs,*_=self.exercise(case)
            self.assertEqual(len(programs),1);self.assertEqual(result['confirmed_completed_inputs'],prefix)
            self.assertIsNone(result['final_capture']);self.assertFalse(result['replay_allowed'])
if __name__=='__main__':unittest.main()
