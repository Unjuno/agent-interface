import hashlib, json, sys
from pathlib import Path
repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); raw=out/'raw'; recorder_root=raw/'recorder'
sys.path.insert(0,str(repo)); sys.path.insert(0,str(repo/'research/integration/standard_mcp_task_ledger_57_v1'))
from recorded_comparison_adapter_v1 import build_measured_run
from effect_receipt_handoff_v1 import adapt_measured_run
cfg=json.loads((out/'conditions.json').read_text(encoding='utf-8-sig'))
receipt=json.loads((raw/'recorder-receipt.json').read_text(encoding='utf-8-sig'))
assert receipt['complete'] is True and receipt['unresolved_attempt_ids']==[] and receipt['unresolved_tool_call_ids']==[]
for cid in (cfg['recorder_call_ids']['observe_before'],cfg['recorder_call_ids']['observe_after']):
    p=raw/f'observation-{cid}.png'; data=p.read_bytes(); ref={'path':f'raw/observation-{cid}.png','sha256':hashlib.sha256(data).hexdigest()}
    dst=recorder_root/ref['path']; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(data)
    if ref not in receipt['raw_refs']: receipt['raw_refs'].append(ref)
(raw/'offline-reconciled-recorder-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def body(filename):
    env=json.loads((raw/filename).read_text(encoding='utf-8-sig'))
    texts=[x['text'] for x in env['result']['content'] if x.get('type')=='text']
    assert len(texts)==1
    return json.loads(texts[0])
observations=[]
for key in ('observe_before','observe_after'):
    cid=cfg['recorder_call_ids'][key]; public=body(f'interface_observe-{cid}.json'); report=public['receipt']['source']['raw_report']; obs=report['observation']
    observations.append({'tool_call_id':cid,'observation_id':report['observation_id'],'target_generation':report['target_generation'],'capture_started_ns':obs['capture_started_ns'],'capture_ended_ns':obs['capture_ended_ns'],'image_sha256':hashlib.sha256((raw/f'observation-{cid}.png').read_bytes()).hexdigest()})
owner=body(f"interface_results-{cfg['recorder_call_ids']['results_exact']}.json")
action=owner['action']; custody=action['completion_custody']; release=custody['completion_release_receipt']; readback=custody['completion_readback']
effect=json.loads((raw/'effect.json').read_text(encoding='utf-8'))
assert action['status']=='completed' and action['release_confirmed'] is True and readback['late_input_horizon_verified'] is True
assert effect['verified'] is True and effect['text']=='a'
all_events=receipt['events']; started=min(e['started_ns'] for e in all_events); ended=max(e['ended_ns'] for e in all_events)
env_bytes=(raw/'environment.json').read_bytes(); scorer_path=out/'source/scorer.py'; fixture_path=out/'source/fixture_app.py'; route_path=out/'source/live_probe.py'
metadata={'schema':'agent-interface/standard-mcp-task-ledger-v1','run_id':cfg['run_id'],'comparison':{'arm':'C','block':1,'order':3,'task_seed':cfg['run_id']},'task':{'task_id':cfg['task_id'],'fixture_sha256':hashlib.sha256(fixture_path.read_bytes()).hexdigest(),'scorer_sha256':hashlib.sha256(scorer_path.read_bytes()).hexdigest()},'source':{'commit':cfg['source_main'],'route_sha256':hashlib.sha256(route_path.read_bytes()).hexdigest()},'environment_sha256':hashlib.sha256(env_bytes).hexdigest(),'model':None}
measurement={'started_ns':started,'ended_ns':ended,'elapsed_ns':ended-started,'phases':[{'name':'other','started_ns':started,'ended_ns':ended,'reason':'one no-provider Win32 fixture lifecycle and public caller'}],'model_delivered_images':[],'local_observations':observations,'effect_attribution':{'effect_observed_ns':effect['effect_observed_ns'],'authority_expiry_ns':custody['deadline_ns'],'release_received_ns':release['monotonic_ns'],'horizon_end_ns':readback['late_input_observation_end_monotonic_ns']}}
measured=build_measured_run(receipt,recorder_root=recorder_root,ledger_metadata=metadata,measurement=measurement)
(raw/'offline-measured-run.json').write_text(json.dumps(measured,indent=2,sort_keys=True)+'\n',encoding='utf-8')
score_event=next(e for e in measured['task_ledger']['events'] if e['kind']=='task_score')
before_state=json.dumps({'text':'','accepted_a_keydowns':0},sort_keys=True,separators=(',',':')).encode()
score={'schema':'agent-interface/task-effect-score-receipt-v1','task_id':cfg['task_id'],'lookup_tool_call_id':cfg['recorder_call_ids']['results_exact'],'action_call_id':owner['call_id'],'action_operation_id':action['operation_id'],'target_generation':action['target_generation'],'scorer_id':score_event['scorer_id'],'scorer_sha256':metadata['task']['scorer_sha256'],'task_success':score_event['task_success'],'state_sha256':score_event['state_sha256'],'before_task_success':False,'before_state_sha256':hashlib.sha256(before_state).hexdigest(),'before_observation':observations[0],'after_observation':observations[1],'effect_interval_ns':{'lower_ns':effect['key_down_accepted_ns'],'upper_ns':effect['effect_observed_ns']}}
score_path=recorder_root/'effect-score.json'; score_path.write_text(json.dumps(score,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
adapted=adapt_measured_run(measured,receipt_root=recorder_root,receipt_path='effect-score.json')
(raw/'offline-adapted-run.json').write_text(json.dumps(adapted,indent=2,sort_keys=True)+'\n',encoding='utf-8')
summary={'status':'PASS_RECORDED_FIXTURE_EFFECT' if adapted['factual_task_success'] and adapted['eligible_task_success'] and action['release_confirmed'] and readback['late_input_horizon_verified'] else 'FAIL_OR_UNKNOWN','run_id':cfg['run_id'],'public_action_call_id':owner['call_id'],'operation_id':action['operation_id'],'target_generation':action['target_generation'],'before_observation_id':observations[0]['observation_id'],'after_observation_id':observations[1]['observation_id'],'release_confirmed':action['release_confirmed'],'late_input_horizon_verified':readback['late_input_horizon_verified'],'horizon_ns':readback['late_input_horizon_ns'],'horizon_samples':readback['late_input_observation_count'],'max_horizon_gap_ns':readback['late_input_max_observed_gap_ns'],'independent_task_success':score_event['task_success'],'public_task_success':action['task_success'],'effect_interval_ns':score['effect_interval_ns'],'effect_timing_status':adapted['timing_status'],'eligible_task_success':adapted['eligible_task_success'],'factual_task_success':adapted['factual_task_success'],'close_status':body(f"interface_close-{cfg['recorder_call_ids']['close_boundary']}.json")['status'],'canonical_reconciliation':'offline completed-owner effect handoff; original live runner failure preserved'}
(raw/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
