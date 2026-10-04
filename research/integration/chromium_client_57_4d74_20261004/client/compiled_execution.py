"""Actual checked-input adapters for a bounded enter/submit compiled graph.
Visual change is a continuation cue, not exact-text verification. The saved
submission scorer is required separately for scientific task correctness.
"""
import copy, hashlib, json, time
from pathlib import Path
from PIL import Image, ImageChops
from compiled_gui_interface_v1 import run as run_compiled

def interface(aliases, scope):
 return {'format':'compiled-gui-interface-v1','interface_id':'integrated-form-compiled',
  'session_scope':scope,'surface':'integrated-form','predicates':['visual_changed','target_valid','exact_saved_title'],
  'symbols':{kind:{'kind':'target_reference','target_reference':aliases[kind],
   'identity_predicate':'target_valid','dependencies':['target_valid']} for kind in ('field','submit')},
  'actions':{'enter':{'target_symbol':'field','operation':'enter_token','expected_effect':{'visual_changed':True}},
   'submit':{'target_symbol':'submit','operation':'submit_form','expected_effect':{'exact_saved_title':True}}},
  'method':{'name':'enter_then_submit','version':'1','initial_state':'empty','max_transitions':2,'max_runtime_ms':10000,
   'states':{'empty':{'branches':[{'when':{'target_valid':True},'outcome':'action','action':'enter','next_state':'filled','reason':None}]},
    'filled':{'branches':[{'when':{'visual_changed':True,'target_valid':True},'outcome':'action','action':'submit','next_state':'submitted','reason':None}]},
    'submitted':{'branches':[{'when':{'exact_saved_title':True},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}

class CompiledExecution:
 def __init__(self, client, task, aliases):
  self.client,self.task,self.aliases=client,task,aliases
  self.previous_image=None;self.current=None;self.authorizations={};self.raw=[];self.events=[]
 def observe(self,payload):
  kind={'empty':'field','filled':'submit'}.get(payload['state'])
  if kind:
   check,program=self.client.check(self.aliases[kind],[12,19] if kind=='field' else [12,7],'compiled-check-'+kind)
  else:
   program=self.client.submit('compiled-final-observation',[{'op':'observe'}]);check=None
  observation=program['observations'][-1]
  image_path=self.client.runtime/Path(observation['image']).name
  with Image.open(image_path) as im: image=im.convert('RGB').copy()
  changed='unknown' if self.previous_image is None else bool(ImageChops.difference(self.previous_image,image).getbbox())
  digest=hashlib.sha256(image_path.read_bytes()).hexdigest()
  title=str(observation.get('context',''))
  predicates={'visual_changed':changed,'target_valid':bool(check and check.get('eligible') is True and check.get('status')=='VALID'),
   'exact_saved_title':'AI INTEGRATED SAVED' in title}
  clock=self.client.clock()
  if clock['sequence']!=observation['sequence']: raise RuntimeError('observation/clock sequence mismatch')
  self.current={'kind':kind,'check':check,'clock':clock,'observation':observation}
  self.previous_image=image
  row={'sequence':observation['sequence'],'captured_ns':observation['capture_ns'],'surface':'integrated-form',
   'predicates':predicates,'evidence_ref':'runtime/'+image_path.name,
   'evidence_digest':hashlib.sha256((digest+json.dumps(predicates,sort_keys=True)).encode()).hexdigest()}
  self.raw.append({'state':payload['state'],'normalized':row,'image_sha256':digest,'target_check':check,'raw_observation':observation})
  return row
 def admit(self,payload):
  row=self.current;kind='field' if payload['action']=='enter' else 'submit'
  check=row['check'];eligible=bool(row['kind']==kind and check and check.get('eligible') is True and check.get('status')=='VALID')
  sequence=row['clock']['sequence'];deadline=row['clock']['runtime_ns']+3_000_000_000
  token=hashlib.sha256((self.task['task_id']+payload['action']+str(sequence)).encode()).hexdigest() if eligible else None
  if eligible:self.authorizations[token]={'action':payload['action'],'sequence':sequence,'deadline':deadline,'used':False}
  return {'eligible':eligible,'status':'revalidated' if eligible else 'missing','authorization':token,'expected_sequence':sequence,'valid_until_ns':deadline if eligible else 0}
 def execute(self,payload):
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
 def run(self):
  receipt=run_compiled(interface(self.aliases,self.task['task_id']),{'observe':self.observe,'admit':self.admit,'execute':self.execute,'verify_effect':self.verify,'cancelled':lambda:False,'journal':self.events.append})
  return {'receipt':receipt,'raw_observations':self.raw,'events':self.events}
