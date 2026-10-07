"""A03 invalidation repair composed through the compiled GUI runtime."""
import copy, hashlib, json, sys, time
from pathlib import Path
from adaptive_acquisition_caller_v3 import run as run_caller
from runtime.core_v1.compiled_gui import run as run_compiled

def interface():
 return {'format':'compiled-gui-interface-v1','interface_id':'composition-a03','session_scope':'private-test-double','surface':'form',
  'predicates':['stage','changed','target'],'symbols':{'field':{'kind':'target_reference','target_reference':'field-ref','identity_predicate':'target','dependencies':['stage','target']}},
  'actions':{'edit':{'target_symbol':'field','operation':'edit','expected_effect':{'changed':True}},'finish':{'target_symbol':'field','operation':'finish','expected_effect':{'stage':2}}},
  'method':{'name':'two-actions','version':'1','initial_state':'open','max_transitions':2,'max_runtime_ms':10000,'states':{
   'open':{'branches':[{'when':{'stage':0,'target':True},'outcome':'action','action':'edit','next_state':'edited','reason':None}]},
   'edited':{'branches':[{'when':{'stage':1,'changed':True,'target':True},'outcome':'action','action':'finish','next_state':'done','reason':None}]},
   'done':{'branches':[{'when':{'stage':2},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}
USAGE={'input_tokens':70,'cached_input_tokens':20,'cache_write_input_tokens':0,'output_tokens':9,'reasoning_output_tokens':2}

def target(): return {'interface':interface()}
def model_result(call_id): return {'call_id':call_id,'output':{'status':'target_reference','target':target()},'usage':copy.deepcopy(USAGE),
 'requested_model':'test-double-model','requested_effort':'none','cost':None,'visible_images_submitted':1,'wait_ns':7000000}
def compiled_execute():
 count=[0]
 def observe(payload):
  count[0]+=1;n=count[0]
  preds=({'stage':0,'changed':False,'target':True} if n==1 else {'stage':1,'changed':True,'target':True} if n==2 else {'stage':2,'changed':True,'target':True})
  return {'sequence':n,'captured_ns':time.perf_counter_ns(),'surface':'form','predicates':preds,'evidence_ref':f'a03-frame-{n}','evidence_digest':f'a03-d{n}'}
 return run_compiled(interface(),{'observe':observe,
  'admit':lambda p:{'eligible':True,'status':'revalidated','authorization':'private-once','expected_sequence':p['observation']['sequence'],'valid_until_ns':time.perf_counter_ns()+1000000000},
  'execute':lambda p:{'status':'completed','action_id':f'a03-action-{count[0]}','effect_ref':f'a03-effect-{count[0]}','release':{'verified':True,'keys_down':[],'buttons_down':[]}},
  'verify_effect':lambda p:{'status':'succeeded','evidence_ref':p['observation']['evidence_ref']},'cancelled':lambda:False,'journal':lambda row:None})
def run_case(case):
 compiled=[]; events=[]; models=[]; calls=[]
 spec={'target':'two-step task','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,'cached_target':{'interface':interface(),'version':'stale'},
  'local_repair_on':['missing'] if case=='local_repair' else [],'repair_on':['missing'],'session_id':'composition-a03-'+case}
 def model(payload):
  r=model_result('a03-model-'+case);models.append(r);return r
 def execute(payload):
  calls.append('execute'); r=compiled_execute();compiled.append(r)
  if r['outcome']=='TASK_SUCCEEDED': return {'status':'completed'}
  if r['outcome']=='SAFE_YIELD': return {'status':'safe_yield','reason':r['reason'],'completed_actions':r['completed_transitions']}
  return {'status':'failed'}
 def repair(payload):
  calls.append('local_repair')
  if case=='local_repair': return {'status':'repaired','target':target(),'receipt':{'schema':'target-handle-semantic-repair-v1'},'model_calls':0,'grants_semantic_authority':False,'grants_input_authority':False}
  return {'status':'missing'}
 def revalidate_model(payload):
  calls.append('post_model_revalidate')
  if case=='changed_after_model': return {'status':'association_changed'}
  obs=payload['current_observation'];cid=payload['model_call_id'];binding=obs['pointer_binding']
  receipt={'schema':'post-model-target-revalidation-v1','status':'CURRENT_PATCH_MATCH_NO_AUTHORITY','model_call_id':cid,
   'model_source_sequence':obs['sequence']-1,'current_sequence':obs['sequence'],'current_capture_ns':obs['capture_ns'],
   'pointer_binding':copy.deepcopy(binding),'grants_semantic_authority':False,'grants_input_authority':False}
  return {'status':'current_patch_match','target':payload['target'],'receipt':receipt,'model_call_id':cid,
   'grants_semantic_authority':False,'grants_input_authority':False}
 adapters={'reuse_revalidate':lambda p:(calls.append('reuse_revalidate') or {'status':'missing'}),
  'local_repair':repair,'acquire_expansion':lambda p:(calls.append('acquire_expansion') or {'frame':'expanded-current'}),
  'expanded_model':model,
  'post_model_observe':lambda p:{'exact':True,'sequence':9,'capture_ns':time.perf_counter_ns(),'pointer_binding':{'focus':1,'surface':1,'geometry':[0,0,640,480]}},
  'post_model_revalidate':revalidate_model,'final_revalidate':lambda p:(calls.append('final_revalidate') or {'status':'revalidated'}),
  'execute':execute,'verify_effect':lambda p:(calls.append('verify_effect') or {'status':'succeeded'}),'journal':events.append}
 ids=iter(['a03-'+case+'-attempt']).__next__
 result=run_caller(spec,adapters,clock=time.perf_counter_ns,id_factory=ids)
 return {'result':result,'compiled':compiled,'model_results':models,'adapter_calls':calls,'journal_events':events}
def main():
 out={'schema':'compiled-caller-composition-a03-v1','source_sha256':{},'cases':{}}
 for name,path in [('caller','research/live_control/adaptive_acquisition_caller_v3.py'),('compiled','runtime/core_v1/compiled_gui.py')]:out['source_sha256'][name]=hashlib.sha256(Path(path).read_bytes()).hexdigest()
 for case in ('local_repair','model_repair','changed_after_model'):out['cases'][case]=run_case(case)
 Path(sys.argv[1]).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
