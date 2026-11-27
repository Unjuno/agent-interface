import copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]);from release_gate import completed_neutral
base=Path(sys.argv[2]);report={}
for route,dirname in [('direct','calc-driver-input-r585'),('compiled','calc-driver-compiled-r586'),('fresh','calc-driver-fresh-r587')]:
 out=base/dirname/'output';producer=json.loads((out/'result.json').read_text());paths={'click':out/'click-result.json'};actions={'click':json.loads(paths['click'].read_text())}
 if route=='compiled':
  transition=producer['method']['method_receipt']['transitions'][0];matches=list((out/'owner').rglob(transition['effect_ref']+'.json'))
  if len(matches)!=1:raise RuntimeError('compiled execution not unique')
  entry=json.loads(matches[0].read_text());
  if entry.get('action_id')!=transition.get('action_id'):raise RuntimeError('action mismatch')
  paths['entry']=matches[0];paths['save']=out/'recovery-save.json';actions['entry']=entry['result'];actions['save']=json.loads(paths['save'].read_text())
 else:
  paths['entry']=out/'fresh-entry.json';paths['save']=out/'fresh-save.json';actions['entry']=json.loads(paths['entry'].read_text());actions['save']=json.loads(paths['save'].read_text())
 observations={}
 for name,receipt in actions.items():
  empty=copy.deepcopy(receipt);empty['execution']['releases']=[]
  missing=copy.deepcopy(receipt);missing['execution']['releases'][0].pop('keys_down',None)
  observations[name]={'source_sha256':hashlib.sha256(paths[name].read_bytes()).hexdigest(),'actual_pass':completed_neutral(receipt),'empty_release_rejected':not completed_neutral(empty),'missing_key_state_rejected':not completed_neutral(missing)}
 report[route]=observations
result={'routes':report,'actual_receipts_all_pass':all(x['actual_pass'] for v in report.values() for x in v.values()),'all_negative_controls_rejected':all(x['empty_release_rejected'] and x['missing_key_state_rejected'] for v in report.values() for x in v.values()),'scope':'offline replay of retained receipts; not new GUI execution'}
out=base/'calc-common-runner-overlay-r588'/'receipt-replay.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'actual_receipts_all_pass':result['actual_receipts_all_pass'],'all_negative_controls_rejected':result['all_negative_controls_rejected'],'receipts':9}))
