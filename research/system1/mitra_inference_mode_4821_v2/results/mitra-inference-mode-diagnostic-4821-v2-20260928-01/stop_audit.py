#!/usr/bin/env python3
"""Independent host-only audit of the one-shot #4947 terminal STOP."""
import hashlib, json, sys
from pathlib import Path
root=Path(__file__).parent
stop=json.loads((root/'formal-01'/'STOP.json').read_text(encoding='utf-8'))
receipt=json.loads((root/'host-evidence-01'/'INVOCATION.json').read_text(encoding='utf-8-sig'))
stderr=(root/'host-evidence-01'/'runner.stderr.txt').read_bytes()
errors=[]
if stop.get('issue')!=4947 or stop.get('allocation')!='mitra-inference-mode-diagnostic-4821-v2-20260928-01': errors.append('STOP_IDENTITY')
if stop.get('stage')!='context_setup' or stop.get('optimizer_step_calls')!=0: errors.append('STOP_STAGE_OR_UPDATES')
if receipt.get('exit_code')!=1 or receipt.get('issue')!=4947: errors.append('INVOCATION_EXIT')
if b"torch._dynamo' has no attribute 'external_utils'" not in stderr: errors.append('TRACEBACK_MISMATCH')
if (root/'formal-01'/'RAW.json').exists() or (root/'audit-01'/'AUDIT.json').exists(): errors.append('UNEXPECTED_RAW_OR_AUDIT')
if len(receipt.get('prelaunch_containers',[]))!=2: errors.append('CONTAINER_RECEIPT')
result={'schema':'mitra-inference-mode-stop-audit-4947-v2','status':'PASS_STOP_AUDITED' if not errors else 'FAIL_STOP_AUDIT','errors':errors,'issue':4947,'allocation':stop.get('allocation'),'stage':stop.get('stage'),'exception_type':stop.get('exception_type'),'optimizer_step_calls':stop.get('optimizer_step_calls'),'model_load_count':0,'prediction_count':0,'raw_present':False,'invocation_exit_code':receipt.get('exit_code'),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'invocation_sha256':hashlib.sha256((root/'host-evidence-01'/'INVOCATION.json').read_bytes()).hexdigest(),'scope':'host-only standard-library audit; no second container or model invocation'}
(root/'audit-01').mkdir(exist_ok=True)
(root/'audit-01'/'STOP_AUDIT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
sys.exit(0 if not errors else 2)

