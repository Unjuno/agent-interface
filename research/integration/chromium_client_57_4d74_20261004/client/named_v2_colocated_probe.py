import sys,json,time,traceback
from pathlib import Path
sys.path.insert(0,'/source/research/live_control')
from integrated_efficiency_client_v2 import RuntimeClient
from compiled_execution_cropocr import CompiledExecution
from adaptive_acquisition_caller_v3 import run as run_caller
client=RuntimeClient(Path('/out/client'),991063,chromium='/usr/bin/chromium');result={};events=[]
started=time.perf_counter_ns()
try:
 client.start();task=client.ready['goal']['tasks'][0];source=client.navigate(task)
 aliases,failure=client.mint(task['layout'],source,{'field_point':[285,400],'submit_point':[376,400]},'caller_graph')
 if failure:raise RuntimeError('mint refused')
 setup_done=time.perf_counter_ns();setup_calls=client.durable_calls
 target={'aliases':aliases,'authority':'reference_only'}
 def revalidate(target):
  for kind in ('field','submit'):
   check,_=client.check(target['aliases'][kind],[12,19] if kind=='field' else [12,7],'caller-revalidate-'+kind)
   if not check.get('eligible'):return {'status':'missing'}
  return {'status':'revalidated'}
 def execute(payload):
  execution=CompiledExecution(client,task,payload['target']['aliases'])
  graph=execution.run();result['graph']=graph
  receipt=graph['receipt']
  if receipt['outcome']=='TASK_SUCCEEDED':return {'status':'completed'}
  if receipt['outcome']=='SAFE_YIELD':return {'status':'safe_yield','reason':receipt['reason'],'completed_actions':receipt['completed_transitions']}
  return {'status':'failed'}
 def verify(payload):
  graph=result.get('graph',{})
  rows=graph.get('raw_observations',[])
  return {'status':'succeeded' if rows and rows[-1]['normalized']['predicates']['exact_saved_title'] is True else 'unavailable'}
 spec={'target':'submit exact task token','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
  'cached_target':target,'local_repair_on':[],'repair_on':[],'session_id':'caller-compiled-991063'}
 result['caller']=run_caller(spec,{'reuse_revalidate':revalidate,'final_revalidate':revalidate,'execute':execute,'verify_effect':verify,'journal':events.append},id_factory=lambda:'caller-compiled-991063')
 result.update({'events':events,'goal':task,'programs':client.programs,'durable_calls':client.durable_calls,
  'setup':{'elapsed_ns':setup_done-started,'durable_calls':setup_calls,'grounding':'fixed points from prior screenshot; human setup cost unavailable'},
  'independent_evaluation':client.finish('finish-caller-compiled-991063'),'elapsed_ns':time.perf_counter_ns()-started,'status':'OBSERVED'})
except Exception as exc:
 result.update({'status':'FAILED','error':{'type':type(exc).__name__,'detail':str(exc)}});traceback.print_exc()
finally:
 try:client.close()
 except Exception as exc:result['cleanup_error']=str(exc)
 Path('/out/result.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'status':result['status'],'caller':result.get('caller'),'error':result.get('error')}))
raise SystemExit(0 if result.get('caller',{}).get('outcome')=='TASK_SUCCEEDED' and 'cleanup_error' not in result else 1)


