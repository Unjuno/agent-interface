import hashlib, importlib.util, json, os, sys, threading, time, uuid
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'driver'))
from wslc_driver import ContainerDriver
run=uuid.uuid4().hex;stop=threading.Event();errors=[];responses=[]
result={'status':'UNKNOWN','run_id':run,'grounding':'fixed_fixture_not_model','started_ns':time.monotonic_ns(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def responder():
 try:
  prior_sequence=None
  for i in (1,2,3):
   qpath=root/'exchange'/f'request-{i}.json'
   while not qpath.exists():
    if stop.wait(.05):return
   q=json.loads(qpath.read_text(encoding='utf-8'));image=root/'exchange'/f'image-{i}.png';digest=hashlib.sha256(image.read_bytes()).hexdigest()
   sequence=q.get('source_sequence')
   if q.get('id')!=f'pilot-{i}' or q.get('image_sha256')!=digest or type(sequence) is not int or (prior_sequence is not None and sequence<=prior_sequence):raise ValueError('request, image or sequence mismatch')
   prior_sequence=sequence
   r={'id':q['id'],'ok':True,'image_sha256':digest,'grounding':{'field_point':[81,151],'submit_point':[82,51]},'fixture':True}
   tmp=root/'exchange'/f'response-{i}.tmp';tmp.write_text(json.dumps(r),encoding='utf-8');os.replace(tmp,root/'exchange'/f'response-{i}.json')
   responses.append({'id':q['id'],'image_sha256':digest,'source_sequence':sequence,'time_ns':time.monotonic_ns()})
 except BaseException as e:errors.append(type(e).__name__)
thread=threading.Thread(target=responder,daemon=True);driver=None
try:
 if any(any((root/name).iterdir()) for name in ('output','exchange')):raise RuntimeError('output or exchange not empty')
 manifest=json.loads((root/'source-manifest.json').read_text(encoding='utf-8'))
 for name,expected in manifest['files'].items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('pre-run source hash mismatch')
 mounts={'/src':(root/'runtime-source',True),'/in':(root/'inputs',True),'/out':(root/'output',False),'/exchange':(root/'exchange',False)}
 env={'PYTHONPATH':'/in/study:/src','PYTHONDONTWRITEBYTECODE':'1','ROUTE':'fresh','RECOVERY_CASE':'clear'}
 driver=ContainerDriver(root/'allocation',run,'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25',['python3','-B','/in/runner.py'],mounts=mounts,environment=env)
 thread.start();result['start']=driver.start(timeout_s=20)
 if result['start'].get('status') in ('running','exited'):result['wait']=driver.wait(timeout_s=80)
 if result.get('wait',{}).get('status')=='exited':
  logs=driver._call(['wslc','container','logs',driver.cid],time.monotonic()+5,allow_stderr=True)
  if logs is not None:(root/'container.stdout').write_bytes(logs)
  result['logs_observed']=logs is not None
  out=root/'output';result['producer_result_exists']=(out/'result.json').exists()
  if (out/'saved.fods').exists():
   spec=importlib.util.spec_from_file_location('archived_oracle',root/'inputs/study/pair_saved_oracle.py');scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
   data=(out/'saved.fods').read_bytes();result['host_rescore']=scorer.score_saved(data);result['saved_sha256']=hashlib.sha256(data).hexdigest()
  result['source_hashes_unchanged']=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==expected for name,expected in manifest['files'].items())
  if result['producer_result_exists']:
   producer=json.loads((out/'result.json').read_text(encoding='utf-8')); result['producer_exit_code']=result['wait'].get('exit_code')
   def neutral(receipt):
    return isinstance(receipt,dict) and receipt.get('verified') is True and receipt.get('keys_down')==[] and receipt.get('buttons_down')==[]
   checks={}
   for name in ('click-result.json','fresh-entry.json','fresh-save.json'):
    try:
     action=json.loads((out/name).read_text(encoding='utf-8'));releases=action.get('execution',{}).get('releases')
     checks[name]=action.get('status')=='completed' and isinstance(releases,list) and bool(releases) and all(neutral(x) for x in releases)
    except (OSError,ValueError,AttributeError):checks[name]=False
   close=producer.get('close',{});result['action_release_checks']=checks
   result['owner_close_verified']=close.get('status')=='closed' and neutral(close.get('release'))
   result['final_neutral_readback']=producer.get('keys_down')==[] and type(producer.get('buttons')) is int and producer['buttons']==0
   try:
    gate=json.loads((out/'stale-gate.json').read_text(encoding='utf-8'))
    result['stale_gate_verified']=gate.get('binding_unchanged') is True and gate.get('prior_programs_or_mints')==[] and gate.get('before_sha256')!=gate.get('after_sha256') and bool(gate.get('before_sha256')) and bool(gate.get('after_sha256'))
   except (OSError,ValueError,AttributeError):result['stale_gate_verified']=False

except BaseException as e:result['error_type']=type(e).__name__;result['error']=str(e)
finally:
 stop.set()
 if thread.ident is not None:thread.join(timeout=3)
 result['fixture_thread_alive']=thread.is_alive();result['fixture_responses']=responses;result['fixture_errors']=errors
 if driver is not None:
  try:result['reconcile']=driver.reconcile(timeout_s=20)
  except BaseException as e:result['reconcile_error_type']=type(e).__name__
 result['ended_ns']=time.monotonic_ns()
 if (result.get('producer_exit_code')==0 and result.get('source_hashes_unchanged') is True
     and result.get('host_rescore',{}).get('pass_effect') is True and len(responses)==3 and not errors
     and not result['fixture_thread_alive'] and all(result.get('action_release_checks',{}).get(n) is True for n in ('click-result.json','fresh-entry.json','fresh-save.json'))
     and result.get('owner_close_verified') is True and result.get('final_neutral_readback') is True and result.get('stale_gate_verified') is True
     and result.get('reconcile',{}).get('remove',{}).get('status')=='observed_absent'):
  result['status']='scoped_fixture_pass'

 (root/'integration-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'start':result.get('start',{}).get('status'),'exit':result.get('wait',{}).get('exit_code'),'score':result.get('host_rescore',{}).get('pass_effect'),'responses':len(responses),'cleanup':result.get('reconcile',{}).get('remove',{}).get('status'),'error':result.get('error_type'),'fixture_errors':errors}))
