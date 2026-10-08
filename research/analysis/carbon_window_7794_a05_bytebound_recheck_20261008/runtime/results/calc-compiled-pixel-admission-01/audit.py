import json,hashlib
from pathlib import Path

def audit(root):
 p=Path(root);report=json.loads((p/'REPORT.json').read_text())
 def require(condition,message):
  if not condition:raise ValueError(message)
 require(report['disposition']=='FAIL_SETUP_INVALID_NATIVE_ALIAS','failure erased')
 commands=sorted((p/'live/commands').glob('*.json'))
 require(len(commands)==2,'command count')
 require(json.loads(commands[1].read_text())=={'op':'mint','alias':'sheet-context','point':[162,172]},'failed alias changed')
 exception=json.loads((p/'live/exception.json').read_text())
 require('target alias must match' in exception['error'],'raw failure missing')
 require(not list((p/'live/bridge').glob('public-dispatch-*')),'unexpected input')
 require(not list((p/'live/bridge').glob('compiled-*-receipt.json')),'unexpected graph')
 require(report['graph_invocations']==0 and report['input_dispatches']==0,'execution counts')
 raw=json.loads((p/'live/replies/001.json').read_text())['reply']['observation']
 art=raw['native']['artifact'];image=p/'live/bridge/images'/Path(art['path']).name
 require(hashlib.sha256(image.read_bytes()).hexdigest()==art['sha256'],'initial image identity')
 require(json.loads((p/'grounding.json').read_text())['source_image_sha256']==art['sha256'],'grounding identity')
 effect=json.loads((p/'live/evaluation.json').read_text())
 require(effect['success'] is False and effect['actual_nonempty_cells']=={} and effect['after_all_owned_processes_terminal'] is True,'saved failure promoted')
 cleanup=json.loads((p/'live/cleanup.json').read_text())
 require(len(cleanup['children'])==3 and all(type(c['returncode']) is int for c in cleanup['children']),'owned cleanup missing')
 require(report['task_success'] is False and report['retry_or_reset'] is False,'outcome changed')
 return {'status':'PASS_SETUP_FAILURE_RECORD','scope':'zero-input alias error; not compiled Calc qualification'}
if __name__=='__main__':
 print(json.dumps(audit(Path(__file__).parent),indent=2))
