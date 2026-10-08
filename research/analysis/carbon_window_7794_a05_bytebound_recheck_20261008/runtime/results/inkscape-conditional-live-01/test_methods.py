import pathlib,tempfile,unittest,time,hashlib,types,json
from unittest.mock import patch
import methods
class MethodsTests(unittest.TestCase):
 def case(self,route,cues,release=True,expired=False,exception=False):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=pathlib.Path(temp.name);(root/'public/images').mkdir(parents=True)
  window=types.SimpleNamespace(id=123);owner=types.SimpleNamespace(state='open',binding_revision=1,targets={'app':123},session_id='test-scope',session=types.SimpleNamespace(recovery_required=False,backend=types.SimpleNamespace(d=None,targets={'app':window})))
  owner.get=lambda:owner.session;calls=[];frames=[]
  def observe(*args,**kwargs):
   i=len(frames);data=str(i).encode();p=root/'public/images'/str(i);p.write_bytes(data);frames.append(data)
   return {'status':'returned','observation':{'native_window_id':123,'region':[0,0,1000,700],'capture_ended_ns':time.monotonic_ns(),'artifact':{'path':str(p),'sha256':hashlib.sha256(data).hexdigest()}}}
  def dispatch(program,**kwargs):
   calls.append(program)
   if exception:raise RuntimeError('uncertain delivery')
   return {'result':{'status':'completed','recovery_required':False,'execution':{'releases':[{'verified':release,'keys_down':[],'buttons_down':[]}]}}}
  owner.dispatch=dispatch;expiry=time.monotonic_ns()+(-1 if expired else 2_000_000_000)
  request={'programs':{name:{'schema':'agent-interface/program-v1','program_id':name,'source':{'observation_seq':0,'binding_revision':1},'authority':{'lease_id':name,'expires_at_ns':expiry},'ops':[{'op':name}],'terminal':{'release_all_required':True}} for name in ['draw','save']}}
  with patch.object(methods,'observe_in_session',observe),patch.object(methods,'retained_cue',side_effect=cues),patch.object(methods,'read_window_title',return_value='two-rectangles.svg - Inkscape'):
   if exception:
    with self.assertRaisesRegex(RuntimeError,'uncertain'):methods.run_method(owner,root,request,1,route,'diagonal_down')
    self.assertEqual(len(calls),1);self.assertTrue((root/'method-exception.json').exists());return None,calls
   result=methods.run_method(owner,root,request,1,route,'diagonal_down')
  return result,calls
 def test_positive_same_input_sequence_and_tail(self):
  outputs=[]
  for route in ['ordinary','compiled']:
   result,calls=self.case(route,[False,True,True]);self.assertEqual(result['common']['outcome'],'TASK_SUCCEEDED');self.assertEqual(result['common']['captures'],3);self.assertEqual([p['source']['observation_seq'] for p in calls],[2,3]);outputs.append([p['ops'] for p in calls])
  self.assertEqual(*outputs)
 def test_unknown_draw_effect_stops_before_save(self):
  for route in ['ordinary','compiled']:
   result,calls=self.case(route,[False,None]);self.assertEqual(result['common']['reason'],'effect_unavailable');self.assertEqual(len(calls),1);self.assertFalse(result['common']['save_dispatched'])
 def test_unverified_release_prevents_capture_and_save(self):
  for route in ['ordinary','compiled']:
   result,calls=self.case(route,[False],release=False);self.assertEqual(result['common']['reason'],'execution_failed');self.assertEqual(result['common']['captures'],1);self.assertEqual(len(calls),1)
 def test_expired_authority_never_dispatches(self):
  for route in ['ordinary','compiled']:
   result,calls=self.case(route,[False],expired=True);self.assertEqual(result['common']['reason'],'authority_unavailable');self.assertEqual(calls,[])
 def test_uncertain_dispatch_exception_once(self):
  for route in ['ordinary','compiled']:self.case(route,[False],exception=True)
if __name__=='__main__':unittest.main()
