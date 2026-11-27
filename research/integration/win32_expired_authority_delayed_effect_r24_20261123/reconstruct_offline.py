from pathlib import Path
import hashlib, importlib.util, json, sys
ROOT=Path(__file__).resolve().parents[3]
PACKET=Path(__file__).resolve().parent
RAW=PACKET/'raw'; OUT=RAW/'offline-reconstruction-r04'; RECORDER=RAW/'recorder'
if OUT.exists(): raise SystemExit('offline reconstruction already exists; preserving it')
OUT.mkdir()
sys.path.insert(0,str(ROOT/'research/integration/standard_mcp_task_ledger_57_v1'))
from recorded_comparison_adapter_v1 import build_measured_run

def readj(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def writej(p,x): p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def event_for(method,index=0):
 rows=[x for x in receipt['events'] if x.get('kind')=='tool_call' and x.get('method')==method]
 if index>=len(rows): raise ValueError(f'expected {method} index {index}, found {len(rows)}')
 return rows[index]
def public_response(event):
 blocks=event['result']['result']['content']
 texts=[b['text'] for b in blocks if b.get('type')=='text' and isinstance(b.get('text'),str)]
 if len(texts)!=1: raise ValueError('expected exact one text result')
 return json.loads(texts[0])
def observation(event):
 obj=public_response(event); rv=obj.get('receipt',{}); raw=rv.get('source',{}).get('raw_report',{})
 if rv.get('authority')!='none' or raw.get('status')!='returned' or raw.get('side_effect_authority') is not False or raw.get('input_dispatched') is not False: raise ValueError('observation does not prove no-input/no-authority')
 obs=raw.get('observation',{}); image=RAW/f"observation-{event['call_id']}.png"; data=image.read_bytes(); digest=hashlib.sha256(data).hexdigest(); art=obs.get('artifact',{})
 if (digest!=art.get('sha256') or len(data)!=art.get('bytes') or art.get('source_raw_sha256')!=obs.get('sha256')): raise ValueError('retained observation image does not match artifact receipt')
 recorder_image=RECORDER/'raw'/image.name
 recorder_image.write_bytes(data)
 receipt['raw_refs'].append({'path':'raw/'+image.name,'sha256':digest})
 return {'tool_call_id':event['call_id'],'observation_id':raw['observation_id'],'target_generation':raw['target_generation'],'capture_started_ns':obs['capture_started_ns'],'capture_ended_ns':obs['capture_ended_ns'],'image_sha256':digest}

cond=readj(PACKET/'conditions.json'); receipt=readj(RAW/'recorder-receipt.json')
if receipt.get('complete') is not True or receipt.get('unresolved_attempt_ids') or receipt.get('unresolved_tool_call_ids'): raise ValueError('source recorder receipt incomplete')
results=readj(RAW/'interface_results-047e67d737ef4b889413a560669cf219.json')
owner=json.loads(results['result']['content'][0]['text']); action=owner['action'];
if not (action.get('status')=='unknown' and action.get('input_dispatched') is True and action.get('release_confirmed') is False and action.get('task_success') is None and action.get('replay_allowed') is False): raise ValueError('source action is not preserved UNKNOWN')
recovery=readj(RAW/'orphan-recovery-api-attempt.json'); rr=recovery['initial_recovery_receipt']['recovery_receipt']
if not (recovery['result_status']=='recovered' and recovery['recovery_release_confirmed'] is True and recovery['recovery_replay_allowed'] is False and rr.get('operation_id')==action['operation_id'] and rr.get('source_target_generation')==action['target_generation'] and rr.get('release_confirmed') is True and rr.get('late_input_horizon_verified') is True): raise ValueError('recovery receipt does not bind exact source action/generation and verified release/horizon')
obs_before=observation(event_for('interface_observe',0))
obs_after_event=event_for('interface_observe',1)
obs_after=observation(obs_after_event)
dispatch_event=event_for('interface_dispatch'); dispatch=public_response(dispatch_event); action_call_id=dispatch.get('call_id')
if not isinstance(action_call_id,str) or owner.get('call_id')!=action_call_id: raise ValueError('dispatch and exact lookup action IDs do not join')
score=next(e for e in receipt['events'] if e.get('kind')=='task_score')
effect=readj(RAW/'effect.json'); fixture=(PACKET/'source/fixture_app.py').read_bytes(); scorer_bytes=(PACKET/'source/scorer.py').read_bytes(); route=(PACKET/'source/live_probe.py').read_bytes(); env_bytes=(RAW/'environment.json').read_bytes()
if score.get('task_success') is not True or effect.get('verified') is not True: raise ValueError('independent fixture score is not verified true')
expiry=owner['standard_program']['authority']['expires_at_ns']; release_ns=rr['late_input_release_received_monotonic_ns']; horizon_end=rr['late_input_observation_end_monotonic_ns']
if not (effect['effect_observed_ns']>expiry and expiry<release_ns<=horizon_end and horizon_end-release_ns>=rr['late_input_horizon_ns']): raise ValueError('effect/recovery timing bounds do not support after-authority-before-release adjudication')
metadata={'schema':'agent-interface/standard-mcp-task-ledger-v1','run_id':cond['run_id'],'comparison':{'arm':'C','block':1,'order':3,'task_seed':cond['run_id']},'task':{'task_id':cond['task_id'],'fixture_sha256':hashlib.sha256(fixture).hexdigest(),'scorer_sha256':hashlib.sha256(scorer_bytes).hexdigest()},'source':{'commit':cond['source_main'],'route_sha256':hashlib.sha256(route).hexdigest()},'environment_sha256':hashlib.sha256(env_bytes).hexdigest(),'model':None}
events=receipt['events']; start=min(e['started_ns'] for e in events); end=max(e['ended_ns'] for e in events)
measurement={'started_ns':start,'ended_ns':end,'elapsed_ns':end-start,'phases':[{'name':'other','started_ns':start,'ended_ns':end,'reason':'offline reconstruction from retained R24 caller journal; no new calls or input'}],'model_delivered_images':[],'local_observations':[obs_before,obs_after],'effect_attribution':{'effect_observed_ns':effect['effect_observed_ns'],'authority_expiry_ns':expiry,'release_received_ns':release_ns,'horizon_end_ns':horizon_end}}
writej(OUT/'recorder-receipt-with-verified-image-refs.json',receipt)
measured=build_measured_run(receipt,recorder_root=RECORDER,ledger_metadata=metadata,measurement=measurement)
writej(OUT/'measured-run.json',measured)
score_event=next(e for e in measured['task_ledger']['events'] if e['kind']=='task_score')
before_state=json.dumps({'text':'','accepted_a_keydowns':0},sort_keys=True,separators=(',',':')).encode()
effect_receipt={'schema':'agent-interface/task-effect-score-receipt-v1','task_id':cond['task_id'],'lookup_tool_call_id':cond['recorder_call_ids']['results_exact'],'action_call_id':action_call_id,'action_operation_id':action['operation_id'],'target_generation':action['target_generation'],'scorer_id':score_event['scorer_id'],'scorer_sha256':hashlib.sha256(scorer_bytes).hexdigest(),'task_success':score_event['task_success'],'state_sha256':score_event['state_sha256'],'before_task_success':False,'before_state_sha256':hashlib.sha256(before_state).hexdigest(),'before_observation':obs_before,'after_observation':obs_after,'effect_interval_ns':{'lower_ns':effect['key_down_accepted_ns'],'upper_ns':effect['effect_observed_ns']}}
score_path=RECORDER/'effect-score-r24-offline.json'; score_bytes=(json.dumps(effect_receipt,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
if score_path.exists() and json.loads(score_path.read_text(encoding='utf-8-sig'))!=effect_receipt: raise ValueError('existing effect-score receipt differs from reconstruction')
if not score_path.exists(): score_path.write_bytes(score_bytes)
writej(OUT/'reconstruction-audit.json',{'schema':'agent-interface/r24-offline-reconstruction-audit-v1','source_action_call_id':action_call_id,'source_operation_id':action['operation_id'],'source_generation':action['target_generation'],'source_action_status':'unknown','source_release_confirmed':False,'source_task_success':None,'source_replay_allowed':False,'independent_factual_task_success':score_event['task_success'],'authority_expiry_ns':expiry,'effect_observed_ns':effect['effect_observed_ns'],'orphan_recovery_release_ns':release_ns,'orphan_recovery_horizon_end_ns':horizon_end,'recovery_horizon_ns':rr['late_input_horizon_ns'],'recovery_horizon_verified':rr['late_input_horizon_verified'],'effect_timing':'derived by separate orphan-recovery handoff', 'eligible_task_success':'derived by separate orphan-recovery handoff','all_provider_usage':'unavailable; provider/model were none','replayed_action':False,'reconstruction_method':'read retained recorder journal, independent fixture score, exact source result, and exact operation/generation-bound public orphan recovery receipt; no live server or input'})
print(json.dumps({'measured_run_validated':True,'independent_task_score':score_event['task_success'],'effect_attribution':measurement['effect_attribution'],'output':str(OUT)},indent=2))
