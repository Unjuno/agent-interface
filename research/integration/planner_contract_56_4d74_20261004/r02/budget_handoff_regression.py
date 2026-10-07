import json,time,importlib.util
from pathlib import Path
raw=json.loads(Path('/prior/formal-output/model-calls/call-011/answer.json').read_text())
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=module('old','/prior/planner_contract_adapter.py');new=module('new','/study/planner_contract_adapter.py')
class Client:
 def __init__(self):self.calls=0;self.programs=[]
 def call(self,spec):
  self.calls+=1;now=time.perf_counter_ns()
  return {'reply':{'records':[{'event':'terminal','id':'construction-only','status':'completed','release':{'verified':True,'keys_down':[],'buttons_down':[]}}]}},now,now

def trial(m):
 client=Client();x=m.CompiledExecution(client,{'task_id':'test','layout':'A','token':'fixture'},{'field':'f','submit':'s'},raw['contract'],[0,0,1,1]);now=time.perf_counter_ns();x.method_deadline=now+raw['contract']['method']['max_runtime_ms']*1000000
 x.current={'kind':'field','check':{'eligible':True,'status':'VALID'},'clock':{'sequence':5,'runtime_ns':now}}
 admission=x.admit({'action':'enter_token'});payload={'action':'enter_token','authorization':admission['authorization'],'expected_sequence':5,'valid_until_ns':min(admission['valid_until_ns'],x.method_deadline)}
 try:terminal=x.execute(payload);reason=None
 except ValueError as e:terminal=None;reason=str(e)
 return {'reason':reason,'native_stub_calls':client.calls,'terminal':terminal,'deadline_preserved':admission['valid_until_ns']<=x.method_deadline}
a=trial(old);b=trial(new);assert a['reason']=='invalid local authorization' and a['native_stub_calls']==0
assert b['reason'] is None and b['native_stub_calls']==1 and b['deadline_preserved']
Path('/out/BUDGET_REGRESSION.json').write_text(json.dumps({'scope':'saved1000ms authored contract / actual adapter / lower-I/O test double; no GUI/model/task-effect claim','old':a,'fixed':b},indent=2));print('PASS old deadline handoff refused; capped new authorization preserved')
