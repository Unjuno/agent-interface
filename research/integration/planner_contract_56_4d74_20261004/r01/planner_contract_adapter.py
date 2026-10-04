"""Actual checked-input adapters for a bounded enter/submit compiled graph.
Visual change is a continuation cue, not exact-text verification. The saved
submission scorer is required separately for scientific task correctness.
"""
import copy, hashlib, json, time, subprocess, re
from pathlib import Path
from PIL import Image, ImageChops
from compiled_gui_interface_v1 import run as run_compiled

class CompiledExecution:
 def __init__(self, client, task, aliases, contract, value_crop):
  self.client,self.task,self.aliases=client,task,aliases
  self.previous_image=None;self.current=None;self.authorizations={};self.raw=[];self.events=[]
  from planner_contract_schema import compile_contract
  self.authored=copy.deepcopy(contract);self.value_crop=list(value_crop);self.last_predicates={}
  if len(self.value_crop)!=4 or not (0<=self.value_crop[0]<self.value_crop[2]<=1280 and 0<=self.value_crop[1]<self.value_crop[3]<=800):raise ValueError('invalid authored OCR crop')
  self.compiled=compile_contract(contract,aliases,'surface-'+str(aliases['field']))
 def observe(self,payload):
  branch=self.compiled['method']['states'][payload['state']]['branches'][0]
  operation=self.compiled['actions'].get(branch['action'],{}).get('operation')
  kind={'enter_token':'field','submit_form':'submit'}.get(operation)
  if kind:
   check,program=self.client.check(self.aliases[kind],[12,19] if kind=='field' else [12,7],'compiled-check-'+kind)
  else:
   program=self.client.submit('compiled-final-observation',[{'op':'observe'}]);check=None
  observation=program['observations'][-1]
  image_path=self.client.runtime/Path(observation['image']).name
  with Image.open(image_path) as im: image=im.convert('RGB').copy()
  boxes={self.task['layout']:self.value_crop}
  crop_path=self.client.root/('ocr-'+str(observation['sequence'])+'.png')
  box=boxes[self.task['layout']]
  image.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4)).save(crop_path)
  ocr_started=time.perf_counter_ns()
  ocr=subprocess.run(['tesseract',str(crop_path),'stdout','--psm','7','-c','tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-'],capture_output=True,text=True,timeout=5)
  ocr_ns=time.perf_counter_ns()-ocr_started
  changed='unknown' if ocr.returncode else self.task['token']==ocr.stdout.strip()
  digest=hashlib.sha256(image_path.read_bytes()).hexdigest()
  title=str(observation.get('context',''))
  predicates={'exact_token_visible':changed,'target_valid':bool(check and check.get('eligible') is True and check.get('status')=='VALID'),
   'exact_saved_title':'AI INTEGRATED SAVED' in title}
  self.last_predicates=predicates
  clock=self.client.clock()
  if clock['sequence']!=observation['sequence']: raise RuntimeError('observation/clock sequence mismatch')
  self.current={'kind':kind,'check':check,'clock':clock,'observation':observation}
  self.previous_image=image
  row={'sequence':observation['sequence'],'captured_ns':observation['capture_ns'],'surface':'integrated-form',
   'predicates':predicates,'evidence_ref':'runtime/'+image_path.name,
   'evidence_digest':hashlib.sha256((digest+json.dumps(predicates,sort_keys=True)).encode()).hexdigest()}
  self.raw.append({'state':payload['state'],'normalized':row,'image_sha256':digest,'target_check':check,'raw_observation':observation,'ocr':{'exit':ocr.returncode,'stdout':ocr.stdout,'stderr':ocr.stderr,'elapsed_ns':ocr_ns}})
  return row
 def _admit_primitive(self,payload):
  row=self.current;kind='field' if payload['action']=='enter' else 'submit'
  check=row['check'];eligible=bool(row['kind']==kind and check and check.get('eligible') is True and check.get('status')=='VALID')
  sequence=row['clock']['sequence'];deadline=row['clock']['runtime_ns']+3_000_000_000
  token=hashlib.sha256((self.task['task_id']+payload['action']+str(sequence)).encode()).hexdigest() if eligible else None
  if eligible:self.authorizations[token]={'action':payload['action'],'sequence':sequence,'deadline':deadline,'used':False}
  return {'eligible':eligible,'status':'revalidated' if eligible else 'missing','authorization':token,'expected_sequence':sequence,'valid_until_ns':deadline if eligible else 0}
 def _execute_primitive(self,payload):
  auth=self.authorizations.get(payload['authorization'])
  if not auth or auth['used'] or auth['action']!=payload['action'] or auth['sequence']!=payload['expected_sequence'] or auth['deadline']!=payload['valid_until_ns']:
   raise ValueError('invalid local authorization')
  auth['used']=True
  kind='field' if payload['action']=='enter' else 'submit'
  steps=[{'op':'pointer_click_target','target_handle':self.aliases[kind],'offset':[12,19] if kind=='field' else [12,7],'button':1,'duration_ms':80}]
  if kind=='field':steps.extend([{'op':'chord','modifier':'Control_L','key':'a'},{'op':'text','text':self.task['token']}])
  steps.append({'op':'settle','quiet_ms':80,'timeout_ms':500})
  result,started,ended=self.client.call({'command':{'op':'submit','expected_sequence':auth['sequence'],'valid_until_ns':auth['deadline'],'steps':steps},'timeout':10})
  records=result['reply']['records'];terminal=next(r for r in records if r.get('event')=='terminal')
  self.client.programs.append({'label':'compiled-'+payload['action'],'started_ns':started,'ended_ns':ended,'terminal':terminal,
   'observations':[r for r in records if r.get('event')=='observation'],'pointer_admissions':[r for r in records if r.get('event')=='pointer_admission'],
   'target_checks':[r for r in records if r.get('event')=='target_handle_checked'],'point_mints':[]})
  release=terminal['release']
  return {'status':terminal['status'],'action_id':terminal['id'],'effect_ref':'terminal:'+terminal['id'],
   'release':{k:release[k] for k in ('verified','keys_down','buttons_down')}}
 def verify(self,payload):
  verdict=all(payload['observation']['predicates'].get(k)==v for k,v in payload['expected_effect'].items())
  return {'status':'succeeded' if verdict else 'failed','evidence_ref':payload['observation']['evidence_ref']}
 def primitive_payload(self,payload):
  operation=self.compiled['actions'][payload['action']]['operation']
  return {**payload,'action':'enter' if operation=='enter_token' else 'submit'}
 def admit(self,payload):
  primitive=self.primitive_payload(payload)
  if primitive['action']=='submit' and self.last_predicates.get('exact_token_visible') is not True:
   return {'eligible':False,'status':'unavailable','authorization':None,'expected_sequence':self.current['clock']['sequence'],'valid_until_ns':0}
  return self._admit_primitive(primitive)
 def execute(self,payload):return self._execute_primitive(self.primitive_payload(payload))
 def run(self):
  receipt=run_compiled(self.compiled,{'observe':self.observe,'admit':self.admit,'execute':self.execute,'verify_effect':self.verify,'cancelled':lambda:False,'journal':self.events.append})
  digest=hashlib.sha256(json.dumps(self.authored,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  return {'receipt':receipt,'raw_observations':self.raw,'events':self.events,'authored_contract':self.authored,'authored_contract_sha256':digest,'compiled_interface':self.compiled,'value_crop':self.value_crop}
