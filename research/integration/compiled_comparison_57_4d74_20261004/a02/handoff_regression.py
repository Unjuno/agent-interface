import sys,json,importlib.util
from pathlib import Path
sys.path.insert(0,'/source/research/live_control');sys.path.insert(0,'/study')
class Client:
 def __init__(self):self.programs=[];self.durable_calls=0;self.runtime=Path('/out')
 def navigate(self,task):return {'image':'fixture.png','sequence':1}
 def mint(self,*args):return {'field':'fixture_field','submit':'fixture_submit'},None
 def check(self,*args):return {'eligible':True,'status':'VALID'},{}
 def execute_handles(self,task,aliases):
  assert aliases['field']=='fixture_field' and aliases['submit']=='fixture_submit'
  return {'status':'completed'}
 def submit(self,*args):
  row={'observations':[{'context':'AI INTEGRATED SAVED'}]};self.programs.append(row);return row
results={}
for label,path in [('old','/old/comparison_runner.py'),('fixed','/study/comparison_runner.py')]:
 spec=importlib.util.spec_from_file_location(label,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.model_call=lambda *a,**k:{'output':{'field_point':[285,400],'submit_point':[376,400]},'thread_ids':['synthetic-handoff'],'usage':None,'requested_model':'fixture','requested_effort':'none','visible_images_submitted':0,'wait_ns':0}
 root=Path('/out')/label;root.mkdir()
 m.run_task(Client(),'B',{'task_id':'task-1','token':'fixture','layout':'A'},None,root)
 row=json.loads((root/'task-1.json').read_text());results[label]={'outcome':row['caller']['outcome'],'reason':row['caller']['reason'],'target':row['caller']['selected_target'],'usage':'synthetic unavailable; no model or GUI used'}
assert results['old']['outcome']=='CALLER_FAILED'
assert results['fixed']['outcome']=='TASK_SUCCEEDED'
assert results['fixed']['target']['aliases']=={'field':'fixture_field','submit':'fixture_submit'}
Path('/out/REGRESSION.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
