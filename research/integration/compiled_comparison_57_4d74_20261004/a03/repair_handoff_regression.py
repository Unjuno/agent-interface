import sys,json,importlib.util
from pathlib import Path
sys.path.insert(0,'/source/research/live_control');sys.path.insert(0,'/study')
BIND={'focus':1,'surface':1,'geometry':[10,10,1050,780]}
class Client:
 def __init__(self):self.programs=[];self.durable_calls=0;self.runtime=Path('/out');self.seq=1
 def observation(self):return {'image':'fixture.png','sequence':self.seq,'capture_ns':self.seq*1000,'pointer_binding':BIND,'exact':True,'context':'AI INTEGRATED SAVED'}
 def navigate(self,task):return self.observation()
 def mint(self,*args):
  aliases={'field':'new_field','submit':'new_submit'}
  self.programs.append({'point_mints':[{'status':'VALID','handle':aliases[k],'patch_sha256':'0'*64} for k in ('field','submit')]})
  return aliases,None
 def check(self,alias,*args):
  self.seq+=1
  check={'eligible':alias.startswith('new'),'status':'VALID' if alias.startswith('new') else 'MISSING','handle':alias,'patch_sha256':'0'*64,'point':[700,558],'sequence':self.seq}
  return check,{'observations':[self.observation()]}
 def execute_handles(self,task,aliases):
  assert aliases=={'field':'new_field','submit':'new_submit'}
  return {'status':'completed'}
 def submit(self,*args):return {'observations':[self.observation()]}
results={}
for label,path in [('old','/old/comparison_runner.py'),('fixed','/study/comparison_runner.py')]:
 spec=importlib.util.spec_from_file_location(label,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.model_call=lambda *a,**k:{'output':{'field_point':[700,558],'submit_point':[688,634]},'thread_ids':['synthetic-repair'],'usage':None,'requested_model':'fixture','requested_effort':'none','visible_images_submitted':0,'wait_ns':0}
 root=Path('/out')/label;root.mkdir()
 cached={'aliases':{'field':'old_field','submit':'old_submit'},'grounding':{},'source':{}}
 try:m.run_task(Client(),'B',{'task_id':'task-4','token':'fixture','layout':'B'},cached,root)
 except RuntimeError:pass
 row=json.loads((root/'task-4.json').read_text());results[label]={'outcome':row['caller']['outcome'],'reason':row['caller']['reason'],'repair_path':row['caller']['repair_path'],'post_model_receipt':row['post_model_receipt'],'evidence_class':'lower-I/O test doubles, no provider/GUI'}
assert results['old']['outcome']=='CALLER_FAILED' and 'mint_records' in results['old']['reason']
assert results['fixed']['outcome']=='TASK_SUCCEEDED' and results['fixed']['repair_path']=='model_reacquisition'
assert results['fixed']['post_model_receipt']['grants_input_authority'] is False
Path('/out/REGRESSION.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
