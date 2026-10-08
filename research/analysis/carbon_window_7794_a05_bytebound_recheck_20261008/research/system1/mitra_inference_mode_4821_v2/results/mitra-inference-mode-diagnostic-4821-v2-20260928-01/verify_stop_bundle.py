#!/usr/bin/env python3
"""Repeatable host-only integrity check for retained #4947 STOP bundle."""
import hashlib, json, sys
from pathlib import Path
root=Path(__file__).parent
errors=[]
def read(name): return (root/name).read_bytes()
try:
 stop=json.loads(read('STOP.json'))
 receipt=json.loads(read('INVOCATION.json'))
 audit=json.loads(read('STOP_AUDIT.json'))
 stderr=read('runner.stderr.txt')
 freeze=json.loads((root.parents[1]/'FREEZE.json').read_bytes())
except Exception as exc:
 print(json.dumps({'status':'FAIL_STOP_BUNDLE_INTEGRITY','errors':[f'READ:{type(exc).__name__}:{exc}']})); raise SystemExit(2)
if stop.get('issue') != 4947 or stop.get('allocation') != freeze.get('allocation'): errors.append('STOP_IDENTITY')
if stop.get('stage') != 'context_setup' or stop.get('optimizer_step_calls') != 0: errors.append('STOP_STAGE_OR_UPDATES')
if stop.get('exception_type') != 'AttributeError' or 'torch._dynamo' not in stop.get('message',''): errors.append('STOP_EXCEPTION')
if receipt.get('issue') != 4947 or receipt.get('exit_code') != 1: errors.append('INVOCATION_EXIT')
if '--gpus' not in receipt.get('command',[]) or 'all' not in receipt.get('command',[]): errors.append('GPU_REQUEST_NOT_RETAINED')
if '--network' not in receipt.get('command',[]) or 'none' not in receipt.get('command',[]): errors.append('NETWORK_POLICY')
if '--read-only' not in receipt.get('command',[]): errors.append('ROOT_READONLY')
if b"torch._dynamo' has no attribute 'external_utils'" not in stderr: errors.append('TRACEBACK_MISMATCH')
if hashlib.sha256(stderr).hexdigest()!=audit.get('stderr_sha256'): errors.append('STDERR_HASH')
if hashlib.sha256(read('INVOCATION.json')).hexdigest()!=audit.get('invocation_sha256'): errors.append('INVOCATION_HASH')
if audit.get('status')!='PASS_STOP_AUDITED' or audit.get('errors') != []: errors.append('POSTHOC_AUDIT_STATUS')
if audit.get('model_load_count')!=0 or audit.get('prediction_count')!=0 or audit.get('optimizer_step_calls')!=0: errors.append('ZERO_MODEL_WORK')
if audit.get('raw_present') is not False: errors.append('RAW_PRESENCE')
result={'schema':'mitra-inference-mode-stop-bundle-check-4947-v1','status':'PASS_STOP_BUNDLE_INTEGRITY' if not errors else 'FAIL_STOP_BUNDLE_INTEGRITY','errors':errors,'issue':4947,'allocation':freeze.get('allocation'),'stage':stop.get('stage'),'exception_type':stop.get('exception_type'),'invocation_exit_code':receipt.get('exit_code'),'model_load_count':audit.get('model_load_count'),'prediction_count':audit.get('prediction_count'),'optimizer_step_calls':audit.get('optimizer_step_calls'),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'invocation_sha256':hashlib.sha256(read('INVOCATION.json')).hexdigest(),'scope':'integrity check of terminal setup STOP only; no scientific result'}
print(json.dumps(result,sort_keys=True,indent=2))
raise SystemExit(0 if not errors else 2)

