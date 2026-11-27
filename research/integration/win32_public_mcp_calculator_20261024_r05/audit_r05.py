"""Audit the frozen R05 standard-caller action and same-session effect receipts."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
P=Path(__file__).resolve().parent; R=P/'run'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
res=read(R/'result.json'); pre=read(R/'preflight.json'); preobs=read(R/'observe-0.json')['parsed']['receipt']['source']['raw_report']; val=read(R/'validation-0.json')['parsed']; disp=read(R/'dispatch-0.json')['parsed']; action=res['action']; custody=action['completion_custody']; postrec=read(R/'post-action-observe-0.json'); post=postrec['parsed']['receipt']['source']['raw_report']; close=read(R/'close-0.json')['parsed']; prog=read(R/'program.json')['program']; postimg=R/'post-action-observe-0-1.png'; clock=read(R/'clock-0.json')['parsed']['monotonic_ns']; capture=post['observation']['capture_started_ns']
checks={
 'conditions_hash_matches_preflight':pre['conditions_sha256']==hashlib.sha256((P/'conditions.json').read_bytes()).hexdigest(),
 'attempt_and_source_match':res['attempt_id']==pre['attempt_id'] and res['source_commit']==pre['source_commit'],
 'pre_action_screen_and_generation_match':preobs['observation']['native_window_id']==55117672 and preobs['observation']['frame']=='screen_physical_px' and preobs['target_generation_consistency']=='matched' and preobs['observation']['region']==[40,32,336,541],
 'program_id_matches_frozen_short_id':prog['program_id']==read(P/'conditions.json')['input_program']['program_id']=='calc-r05-314plus728' and len(prog['program_id'])<=64,
 'static_validation_passed_once':val['status']=='valid' and val['static_valid'] is True,
 'one_dispatch_call_bound':disp['status']=='pending' and disp['call_id']==res['call_id'],
 'action_completed_and_generation_bound':action['status']=='completed' and action['operation_id']==res['operation_id'] and action['target_generation']==preobs['target_generation'],
 'release_verified_and_neutral':action['release_confirmed'] is True and custody['completion_release_receipt']['verified'] is True and custody['completion_readback']['neutral'] is True and custody['producer_exit_code']==0 and all(not custody['completion_release_receipt'][k] for k in ('keys_down','keys_unknown','buttons_down','buttons_unknown')),
 'no_recovery_or_replay':action['result']['recovery_required'] is False and action['replay_allowed'] is False,
 'same_session_post_observation_matches_generation':post['observation']['native_window_id']==55117672 and post['observation']['frame']=='screen_physical_px' and post['observation']['region']==[40,32,336,541] and post['target_generation']==action['target_generation']==res['post_action_observation']['target_generation'] and post['target_generation_consistency']=='matched',
 'post_image_hash_matches_raw_capture':postimg.is_file() and hashlib.sha256(postimg.read_bytes()).hexdigest()==post['observation']['artifact']['sha256'],
 'post_observation_within_90s_of_pre_dispatch_clock':0<=capture-clock<=90_000_000_000,
 'session_closed_without_unresolved_calls':close['status']=='closed' and close['session']['state']=='closed' and close['session']['unresolved_call_ids']==[],
 'task_success_left_unpromoted':res.get('task_success') is None and action.get('task_success') is None,
 'integrated_runner_status_is_post_observed':res['status']=='ACTION_COMPLETED_RELEASE_CONFIRMED_POST_OBSERVED',
}
report={'schema':'win32-public-mcp-calculator-r05-audit-v1','attempt_id':res['attempt_id'],'checks':checks,'passed':sum(bool(v) for v in checks.values()),'total':len(checks),'disposition':'PASS_SCOPED for one native Calculator task action, normal completion release, and same-session generation-matched visual effect; no blocked-I/O/recovery or independent semantic oracle claim','visual_assessment':'Manual inspection of the SHA-256-bound same-session post-action screenshot shows Calculator Standard mode with display 1,042 after the frozen clear + 314 + 728 program. Runtime task_success remains null.','task_success':None,'timing_ns':{'pre_dispatch_clock':clock,'action_started':action['result']['execution']['started_ns'],'producer_exit':custody['completion_readback']['producer_exit_confirmed_ns'],'neutral_completion_readback':custody['completion_readback']['observed_monotonic_ns'],'post_capture_started':capture,'clock_to_post_capture':capture-clock},'scope_limits':['One target, one task, one attempt.','No cancellation, blocked platform I/O, bounded recovery, MAP01, matched efficiency, reliability estimate, or semantic application oracle was tested.','The action used one terminal release path and reports replay denied.']}
(R/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':report['passed'],'total':report['total'],'failed':[k for k,v in checks.items() if not v],'release_confirmed':action['release_confirmed'],'post_ms_from_clock':round((capture-clock)/1e6,3),'task_success':None},ensure_ascii=False))
