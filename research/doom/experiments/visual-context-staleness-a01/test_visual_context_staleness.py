import ast,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from action_validity_admission_v1 import SNAPSHOT_FORMAT,evaluate_action_validity
from doom_action_validity_contract_v1 import bindings_equal_exact,build_contract
from final_action_admission_v2 import decide_final_admission,record_action_validity
from persistent_planner_adapter_v2 import PersistentPlannerAdapter
FIXTURE=json.loads((ROOT/'inputs/fixture.json').read_text(encoding='utf-8'))
BINDING=FIXTURE['pair']['2']['typed_observation']['pointer_binding']
ACTION={'commands':[{'action':'fire','extent':'short'}]}
AUTHORED={'critical_health_minimum':45,'maximum_health_loss':8,'minimum_ammo':1,'max_current_age_ms':700}
SCHEMA={'type':'object','required':['commands'],'additionalProperties':False,'properties':{'commands':{'type':'array','minItems':1,'items':{'type':'object'}}}}
def load_controller():
 spec=importlib.util.spec_from_file_location('visual_guard',ROOT/'observable_signal_guard_v2.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 tree=ast.parse((ROOT/'map01_overlap_controller_v39.py').read_text(encoding='utf-8'));top={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 names=('guard_spec','ammo_guard_spec','_typed_json_equal','_signal_pair_matches','_signal_pair_content_matches','DoomCoverSignalPairMonitor','build_cover_monitor','begin_model_turn','final_admission_from_planner_result','prepare_action_admission')
 ns={'json':json,'time':__import__('time'),'ObservableSignalGuard':guard.ObservableSignalGuard,'ObservableSignalPolicyMonitor':guard.ObservableSignalPolicyMonitor,'MAX_AUTHORED_HEALTH_LOSS':20,'build_action_contract':build_contract,'bindings_equal_exact':bindings_equal_exact,'SNAPSHOT_FORMAT':SNAPSHOT_FORMAT,'evaluate_action_validity':evaluate_action_validity,'record_action_validity':record_action_validity,'decide_final_admission':decide_final_admission,'win':lambda p:str(p)}
 exec(compile(ast.Module(body=[top[n] for n in names],type_ignores=[]),str(ROOT/'map01_overlap_controller_v39.py'),'exec'),ns);return ns
class FakeClient:
 def __init__(self,monitor,current,events):self.monitor=monitor;self.current=current;self.events=events;self.inputs=[]
 def start_thread(self,**kw):return {'thread':{'id':'visual-a01-thread'}}
 def start_turn(self,thread_id,inputs,**kw):self.inputs.append(inputs);self.events.append('turn_started');return {'turn':{'id':'visual-a01-turn'}}
 def wait_turn_completed(self,thread_id,turn_id,timeout=120):
  self.events.append('new_frame_observed');self.invalidation=self.monitor.observe(self.current)
  if self.invalidation is None:self.events.append('monitor_preserved_pending_turn')
  else:self.events.append('monitor_invalidated')
  return {'turn':{'status':'completed','items':[{'type':'agentMessage','text':json.dumps(ACTION)}]}}
 def latest_turn_usage(self,thread_id,turn_id):return {'input_tokens':0,'output_tokens':0}
class SignalReader:
 def __init__(self,name):self.name=name
 def read(self,obs):return {'format':'observable-signal-v1','status':'observed','signal_id':self.name,'value':obs[self.name],'sequence':obs['sequence'],'capture_ns':obs['capture_ns'],'binding':obs['pointer_binding']}
class VisualContextStalenessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.f=load_controller()
 def run_case(self,copy_hash):
  f=self.f;source_t=FIXTURE['pair']['2']['typed_observation'];current_t=copy.deepcopy(FIXTURE['pair']['3']['typed_observation'])
  if copy_hash:current_t['frame_rgb_sha256']=source_t['frame_rgb_sha256']
  source={'event':'observation','sequence':source_t['sequence'],'capture_ns':source_t['capture_ns'],'pointer_binding':source_t['pointer_binding'],'health':source_t['signals']['health']['value'],'ammo':source_t['signals']['ammo']['value'],'frame_rgb_sha256':source_t['frame_rgb_sha256']}
  now={'event':'observation','sequence':current_t['sequence'],'capture_ns':current_t['capture_ns'],'pointer_binding':current_t['pointer_binding'],'health':current_t['signals']['health']['value'],'ammo':current_t['signals']['ammo']['value'],'frame_rgb_sha256':current_t['frame_rgb_sha256']}
  hr,ar=SignalReader('health'),SignalReader('ammo');monitor,_=f['build_cover_monitor'](hr,source,{'signal_id':'health','critical_health_minimum':45,'maximum_health_loss':8,'max_source_age_ms':1000},'visual-a01',ammo_reader=ar,requires_ammo=True)
  events=[];client=FakeClient(monitor,current_t,events);planner=PersistentPlannerAdapter(client,model='frozen-mock',effort='low',cwd='.',base_instructions='visual-context staleness fixture');planner.start_session()
  source_frame=ROOT/'inputs/002.png';current_frame=ROOT/('inputs/002.png' if copy_hash else 'inputs/003.png')
  frame_info=json.loads((ROOT/'inputs/frame-audit.json').read_text(encoding='utf-8'))
  self.assertEqual(hashlib.sha256(source_frame.read_bytes()).hexdigest(),frame_info['frames']['002.png']['file_sha256'])
  self.assertEqual(hashlib.sha256(current_frame.read_bytes()).hexdigest(),frame_info['frames'][current_frame.name]['file_sha256'])
  handle=f['begin_model_turn'](planner,ROOT,'inputs/002.png',[],source['health'],source['ammo'],{},SCHEMA);result=planner.await_turn(handle)
  self.assertEqual(Path(client.inputs[0][1]['path']).name,'002.png')
  terminal=current_t['capture_ns']+50_000_000;receipt=f['final_admission_from_planner_result'](result,terminal,None,terminal+1)
  admitted=f['prepare_action_admission'](receipt,result.answer,AUTHORED,hr.read(source),ar.read(source),hr.read(now),ar.read(now),terminal+2)
  return {'source_frame_rgb_sha256':source_t['frame_rgb_sha256'],'current_frame_rgb_sha256':current_t['frame_rgb_sha256'],'source_png_sha256':frame_info['frames']['002.png']['file_sha256'],'current_png_sha256':frame_info['frames'][current_frame.name]['file_sha256'],'source_health_ammo':[source['health'],source['ammo']],'current_health_ammo':[now['health'],now['ammo']],'monitor_invalidation':client.invalidation,'soft_events':monitor.soft_event_count,'answer_eligible':result.answer_eligible,'final_status':admitted['status'],'final_reason':admitted['action_validity']['reason'],'executor_admission':admitted['executor_admission'],'input_authority_admitted':admitted['input_authority_admitted'],'events':events}
 def test_actual_changed_rgb_hash_with_same_hud_does_not_invalidate_or_block_action(self):
  r=self.run_case(False);self.assertNotEqual(r['source_frame_rgb_sha256'],r['current_frame_rgb_sha256']);self.assertNotEqual(r['source_png_sha256'],r['current_png_sha256']);self.assertEqual(r['source_health_ammo'],r['current_health_ammo']);self.assertIsNone(r['monitor_invalidation']);self.assertTrue(r['answer_eligible']);self.assertEqual(r['final_status'],'READY_FOR_FRESH_EXECUTOR_ADMISSION');self.assertIsNone(r['executor_admission']);self.assertFalse(r['input_authority_admitted']);print('VISUAL_CHANGED='+json.dumps(r,sort_keys=True))
 def test_same_frame_hash_control_has_same_admission_result(self):
  r=self.run_case(True);self.assertEqual(r['source_frame_rgb_sha256'],r['current_frame_rgb_sha256']);self.assertIsNone(r['monitor_invalidation']);self.assertTrue(r['answer_eligible']);self.assertEqual(r['final_status'],'READY_FOR_FRESH_EXECUTOR_ADMISSION');self.assertIsNone(r['executor_admission']);self.assertFalse(r['input_authority_admitted']);print('VISUAL_CONTROL='+json.dumps(r,sort_keys=True))
if __name__=='__main__':unittest.main(verbosity=2)
