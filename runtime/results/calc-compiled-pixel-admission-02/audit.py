import hashlib,json
from pathlib import Path
def audit(root):
 p=Path(root)
 def require(value,message):
  if not value:raise ValueError(message)
 report=json.loads((p/'REPORT.json').read_text())
 require(report['disposition']=='FAIL_BACKEND_CONSTRAINT_HOME_KEY','failure erased')
 require(report['task_success'] is False and report['completed_graph_transitions']==0,'success promoted')
 require(len(list((p/'live/commands').glob('*.json')))==4,'command count')
 req=json.loads((p/'live/commands/003.json').read_text())
 require(req['op']=='run','missing attempted graph')
 reply=json.loads((p/'live/replies/003.json').read_text())['reply']
 require(reply['receipt']['outcome']=='RUNTIME_FAILED' and reply['receipt']['completed_transitions']==0,'frozen receipt changed')
 require(len(reply['receipt']['observations'])==1,'graph observations')
 execution=list((p/'live/bridge').glob('*-execution.json'))
 require(len(execution)==1,'execution count')
 raw=json.loads(execution[0].read_text())['result']
 require(raw['status']=='refused' and raw['error']=='BACKEND_CONSTRAINT' and 'HOME' in raw['detail'],'wrong refusal')
 require(raw['program_execution_started'] is False and raw['program_emissions']==0 and raw['backend_emissions']==0,'unexpected input')
 require(raw['release']['verified'] is True and raw['release']['keys_down']==[] and raw['release']['buttons_down']==[],'raw cleanup discarded')
 event=next(x for x in reply['receipt']['critical_events'] if x['event']=='action_terminal')
 require(event['release_verified'] is False,'historical diagnostic overwritten')
 probe=json.loads((p/'normalization-probe.json').read_text())
 require(probe['raw_file_sha256']==hashlib.sha256(execution[0].read_bytes()).hexdigest(),'probe raw identity')
 require(probe['outcome']=='SAFE_YIELD' and probe['reason']=='execution_failed' and probe['actual_gui_rerun'] is False,'probe outcome')
 require(probe['terminal']['release']['verified'] is True and 'input_dispatched' not in probe['terminal'],'invented delivery/erased release')
 require(probe['probe_backend_inputs']==[],'probe input')
 for f in (p/'live/bridge').glob('observation-*.json'):
  n=json.loads(f.read_text());a=n['native']['artifact'];image=p/'live/bridge/images'/Path(a['path']).name
  require(hashlib.sha256(image.read_bytes()).hexdigest()==a['sha256'],'capture identity')
 effect=json.loads((p/'live/evaluation.json').read_text())
 require(effect['success'] is False and effect['actual_nonempty_cells']=={} and effect['after_all_owned_processes_terminal'] is True,'saved failure changed')
 cleanup=json.loads((p/'live/cleanup.json').read_text())
 require(len(cleanup['children'])==3 and all(type(c['returncode']) is int for c in cleanup['children']),'cleanup missing')
 return {'status':'PASS_RETAINED_BACKEND_REFUSAL_AND_NORMALIZATION','scope':'failed real trial plus inert result conversion; no live success/performance proof'}
if __name__=='__main__':print(json.dumps(audit(Path(__file__).parent),indent=2))
