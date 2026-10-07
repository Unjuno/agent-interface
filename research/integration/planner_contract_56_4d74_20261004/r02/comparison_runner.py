"""Prospective matched runner. Not executed until protocol/source freeze."""
import hashlib,json,time,sys,traceback
from pathlib import Path
sys.path.insert(0,'/source/research/live_control')
from integrated_efficiency_client_capacity_v3 import RuntimeClient
from adaptive_acquisition_caller_v3 import run as run_caller,ModelFailure
from post_model_target_revalidation_v1 import receipt as current_patch_receipt
from planner_contract_adapter import CompiledExecution
from planner_contract_schema import CONTRACT, array, compile_contract
OUT=Path('/out');MODEL_REQUESTS=[];serial=0
POINT={'type':'array','items':{'type':'integer','minimum':0,'maximum':1279},'minItems':2,'maxItems':2}
def schema(arm):
 properties={'field_point':POINT,'submit_point':POINT}
 if arm=='C':properties.update(contract=CONTRACT,value_crop=array({'type':'integer','minimum':0,'maximum':1279},4,4))
 return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2))
def model_call(arm,prompt,image=None):
 global serial
 serial+=1
 if serial>40:raise RuntimeError('model-attempt budget exhausted')
 name=f'call-{serial:03d}';request=OUT/'requests'/(name+'.request.json');response=request.with_suffix('.response.json')
 value={'call_id':name,'arm':arm,'schema':schema(arm),'prompt':prompt,'image_relative':None if image is None else str(image.relative_to(OUT)),
  'image_sha256':None if image is None else hashlib.sha256(image.read_bytes()).hexdigest()}
 tmp=request.with_suffix('.tmp');dump(tmp,value);tmp.replace(request)
 deadline=time.monotonic()+120
 while not response.exists():
  if time.monotonic()>deadline:raise ModelFailure('host model response deadline',visible_images_submitted=1 if image else 0)
  time.sleep(.1)
 result=json.loads(response.read_text());MODEL_REQUESTS.append(result);dump(OUT/'model-responses.json',MODEL_REQUESTS)
 if not result['transport_ok']:raise ModelFailure('model transport/output failed',call_id=(result['thread_ids'][0] if result['thread_ids'] else None),usage=result.get('usage'),visible_images_submitted=result['visible_images_submitted'],wait_ns=result['wait_ns'])
 import jsonschema
 try:jsonschema.validate(result['output'],schema(arm))
 except Exception as e:raise ModelFailure('schema output invalid: '+str(e),call_id=result['thread_ids'][0],usage=result.get('usage'),visible_images_submitted=result['visible_images_submitted'],wait_ns=result['wait_ns'],typed_status='FAILED_OUTPUT')
 if arm=='C':
  try:
   compile_contract(result['output']['contract'],{'field':'precheck-field','submit':'precheck-submit'},'validation-only')
   x0,y0,x1,y1=result['output']['value_crop']
   if not (0<=x0<x1<=1280 and 0<=y0<y1<=800):raise ValueError('invalid crop bounds')
  except ValueError as e:raise ModelFailure('contract output invalid: '+str(e),call_id=result['thread_ids'][0],usage=result.get('usage'),visible_images_submitted=result['visible_images_submitted'],wait_ns=result['wait_ns'],typed_status='FAILED_OUTPUT')
 for point in ('field_point','submit_point'):
  if not 0<=result['output'][point][1]<800:raise ModelFailure('grounding outside screenshot',call_id=result['thread_ids'][0],usage=result['usage'],visible_images_submitted=result['visible_images_submitted'],wait_ns=result['wait_ns'],typed_status='FAILED_OUTPUT')
 return result

def run_task(client,arm,task,cached,root):
 begin=time.perf_counter_ns();program_start=len(client.programs);durable_start=client.durable_calls
 source=client.navigate(task);resolved={};graph=None;events=[];current_receipt=None;model_failed=False
 def acquire(payload):return {'source':source}
 def grounding(payload):
  nonlocal model_failed
  image=client.runtime/Path(source['image']).name
  prompt='Locate the visible editable Value field and Save button in this current screenshot. Give source-image pixel points, field point in the empty right half away from caret. Authorized token is '+task['token']+'. Do not use tools. Return only the schema object.'
  if arm=='C':prompt+=' Author the contract state graph yourself; it is executed directly, not replaced by a template. Primitive vocabulary: enter_token on field; submit_form on submit. Predicates: target_valid (fresh target identity), exact_token_visible (OCR equals authorized token), exact_saved_title (independent visible saved title cue). Include expected effect exact_token_visible=true for enter and exact_saved_title=true for submit, require exact_token_visible=true before submit and exact_saved_title=true for completion. Use one branch per state, null action/next_state/reason for complete, null reason for action. Choose the actual field text interior value_crop=[left,top,right,bottom] in full screenshot pixels; exclude border/label, include full possible value and margin. Names, states, transitions, action targets and conditions are your contract, bounded by schema. Do not use a fixed method enum.'
  try:m=model_call(arm,prompt,image)
  except ModelFailure:model_failed=True;raise
  target={'grounding':m['output'],'source':source,'aliases':None,'model_call_id':m['thread_ids'][0]}
  return {'call_id':m['thread_ids'][0],'output':{'status':'target_reference','target':target},'usage':m['usage'],'requested_model':m['requested_model'],'requested_effort':m['requested_effort'],'cost':None,'visible_images_submitted':m['visible_images_submitted'],'wait_ns':m['wait_ns']}
 def revalidate(target):
  for kind in ('field','submit'):
   check,_=client.check(target['aliases'][kind],[12,19] if kind=='field' else [12,7],'reuse-check-'+kind)
   if not check.get('eligible'):return {'status':'missing' if check['status']=='MISSING' else 'stale'}
  resolved.update(target);return {'status':'revalidated'}
 def mint(target):
  if target.get('aliases') is None:
   start=len(client.programs);aliases,failure=client.mint(task['layout'],target['source'],target['grounding'],'p'+arm.lower()+task['task_id'].replace('-',''))
   if failure:return {'status':'unavailable'}
   target['aliases']=aliases;target['mint_records']=[m for p in client.programs[start:] for m in p['point_mints']]
  resolved.update(target);verdict=revalidate(target)
  return {'status':'revalidated','target':target} if verdict['status']=='revalidated' else verdict
 def post_observe(payload):
  target=payload['target'];verdict=mint(target)
  if verdict['status']!='revalidated':raise RuntimeError('post-model mint refused')
  check,program=client.check(target['aliases']['field'],[12,19],'post-model-field')
  return {**program['observations'][-1],'resolution':check,'checked_target':target}
 def post_revalidate(payload):
  nonlocal current_receipt
  observation=payload['current_observation'];target=observation['checked_target']
  try:current_receipt=current_patch_receipt(target['mint_records'][0],observation['resolution'],target['source'],observation,payload['model_call_id'])
  except ValueError:return {'status':'association_changed'}
  return {'status':'current_patch_match','target':target,'receipt':current_receipt,'model_call_id':payload['model_call_id'],'grants_semantic_authority':False,'grants_input_authority':False}
 def execute(payload):
  nonlocal graph
  target=payload['target'];resolved.update(target)
  if arm=='A':execution=client.execute_plain(task,target['grounding'])
  elif arm=='B':execution=client.execute_handles(task,target['aliases'])
  else:
   graph=CompiledExecution(client,task,target['aliases'],target['grounding']['contract'],target['grounding']['value_crop']).run();receipt=graph['receipt']
   execution={'status':'completed'} if receipt['outcome']=='TASK_SUCCEEDED' else {'status':'safe_yield','reason':receipt['reason'],'completed_actions':receipt['completed_transitions']}
  if execution['status']=='safe_yield':return {k:execution[k] for k in ('status','reason','completed_actions')}
  return {'status':execution['status']}
 def verify(payload):
  program=client.submit('verify-saved-title',[{'op':'observe'}]);observation=program['observations'][-1]
  return {'status':'succeeded' if 'AI INTEGRATED SAVED' in str(observation.get('context','')) else 'failed'}
 if arm=='D':
  client.submit('deterministic-enter-submit',[{'op':'chord','modifier':'Control_L','key':'a'},{'op':'text','text':task['token']},{'op':'key','key':'Return'},{'op':'settle','quiet_ms':80,'timeout_ms':500}])
  result={'outcome':'TASK_SUCCEEDED' if verify(None)['status']=='succeeded' else 'TASK_NOT_VERIFIED','model_call_ledger':[],'setup':'known-form autofocus keyboard route; no weaker replacement task'}
 else:
  reuse=arm in ('B','C') and cached is not None
  spec={'target':'submit exact task token','route':'reuse' if reuse else 'cold','coarse_origin':'caller_provided','provided_coarse':None if reuse else {'source_sequence':source['sequence']},'cached_target':cached if reuse else None,'local_repair_on':[],'repair_on':['missing','stale'] if arm in ('B','C') else [],'session_id':arm}
  result=run_caller(spec,{'observe_source':lambda p:source,'acquire_anchor':acquire,'anchor_model':grounding,'reuse_revalidate':revalidate,'acquire_expansion':acquire,'expanded_model':grounding,'post_model_observe':post_observe,'post_model_revalidate':post_revalidate,'final_revalidate':mint if arm!='A' else lambda t:(resolved.update(t) or {'status':'revalidated'}),'execute':execute,'verify_effect':verify,'journal':events.append},id_factory=lambda:arm+task['task_id'])
 row={'task':task,'caller':result,'graph':graph,'post_model_receipt':current_receipt,'source':source,'programs':client.programs[program_start:],'durable_calls':client.durable_calls-durable_start,'elapsed_ns':time.perf_counter_ns()-begin,'events':events,'provider_failed':model_failed}
 dump(root/(task['task_id']+'.json'),row)
 if model_failed:raise RuntimeError('provider failure; formal allocation stops without retry')
 if result['outcome']=='CALLER_FAILED':raise RuntimeError('caller implementation failure; stop allocation without retry')
 return resolved if result['outcome']=='TASK_SUCCEEDED' and arm in ('B','C') else cached

def main():
 plan=json.loads(Path('/study/PROTOCOL.json').read_text())
 for index,block in enumerate(plan['blocks'],1):
  for arm in block['order']:
   root=OUT/f'block-{index}'/arm
   # Fresh endpoint compatibility call is outside caller but kept/charged per arm/block.
   if arm!='D':dump(root/'schema-preflight.json',model_call(arm,'Return valid field_point=[285,400], submit_point=[376,400], with a bounded valid contract and value_crop=[0,0,1,1] if required. This crop is a valid dummy rectangle for schema compatibility, not a GUI target. For contract: symbols use both roles field/submit; enter_token targets field and expects exact_token_visible=true; submit_form targets submit and expects exact_saved_title=true; the submit branch requires exact_token_visible=true; completion requires exact_saved_title=true. Use one branch per state, null reason for action, null action/next_state/reason for complete. This is endpoint schema compatibility only; no GUI or task authorization.'))
   cached=None
   with RuntimeClient(root/'client',block['seed'],chromium='/usr/bin/chromium') as client:
    try:
     for task in client.ready['goal']['tasks']:cached=run_task(client,arm,task,cached,root)
    finally:
     try:dump(root/'independent-evaluation.json',client.finish(f'finish-{index}-{arm}'))
     except Exception as scoring_error:dump(root/'SCORING_UNAVAILABLE.json',{'type':type(scoring_error).__name__,'detail':str(scoring_error)})
if __name__=='__main__':
 try:main()
 except Exception as error:dump(OUT/'STOP.json',{'type':type(error).__name__,'detail':str(error),'retry':False});traceback.print_exc();raise

