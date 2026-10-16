#!/usr/bin/env python3
"""Independent raw-only audit; never reruns the candidate."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
f=json.loads((root/'FREEZE.json').read_text());r=json.loads((root/'results/A01/RAW.json').read_text())
a=r['arms']['active_hard_health_invalidation']; ev=a['executor_events']
accepted=a['executor_acceptance']; press=a['key_press_event']; release=a['key_release_event']; planner=a['final_admission']['planner_terminal']; term=a['executor_terminal']; owner=a['backend_release_transitions'][0]; receipt=owner['owner_thread_keyup_receipt']
checks={
 'candidate_complete_no_errors_clean_xvfb':r['status']=='CANDIDATE_COMPLETE' and not r['errors'] and r['cleanup'].get('xvfb_exit')==0 and not any(k.endswith('_error') for k in r['cleanup']),
 'frozen_sources_match':all(hashlib.sha256((root/'SOURCE'/n).read_bytes()).hexdigest()==h for n,h in f['source_sha256'].items()),
 'frozen_inputs_match':all(hashlib.sha256((root/'INPUTS'/n).read_bytes()).hexdigest()==h for n,h in f['input_sha256'].items()),
 'candidate_hash_match':hashlib.sha256((root/'SOURCE/candidate.py').read_bytes()).hexdigest()==f['candidate_sha256'],
 'watcher_started_before_acceptance':a['key_release_observer_started_ns']<accepted['accepted_ns'],
 'accepted_before_keypress_and_key_was_down':accepted['accepted_ns']<press['observed_ns'] and a['key_down_when_observation_arrived'] is True,
 'hard_invalidation_cancel_matched':a['monitor_invalidation']['outcome']['status']=='HARD_INVALIDATED' and a['executor_cancel_matched'] is True,
 'cancelled_terminal_has_verified_owner_keyup':term['status']=='cancelled' and term['release']['verified'] is True and receipt['event']=='owner_explicit_keyup' and receipt['server_keyup_verified'] is True and receipt['server_sync_completed'] is True and receipt['server_key_down_after_keyup'] is False,
 'independent_keyrelease_before_planner_return':release is not None and release['type']==3 and release['keycode']==a['keycode'] and release['observed_ns']<planner['terminal_observed_ns'],
 'planner_ineligible_final_admission_rejected':a['planner_answer_eligible'] is False and a['planner_cancellation_requested'] is True and a['final_admission']['status']=='REJECTED_POLICY_INVALIDATED' and a['final_admission']['input_authority_admitted'] is False,
 'executor_and_owner_stopped':a['executor_active_after_terminal'] is False and a['owner_stopped'] is True and a['owner_thread_alive'] is False,
}
out={'schema':'v39-executor-cancel-active-key-xvfb-a02-audit-v1','decision':'PASS_METHOD_SCOPED' if all(checks.values()) else 'STOP','checks':checks,'timing_ns':{'watcher_started':a['key_release_observer_started_ns'],'executor_accepted':accepted['accepted_ns'],'x_keypress_observed':press['observed_ns'],'x_keyrelease_observed':release['observed_ns'] if release else None,'planner_return':planner['terminal_observed_ns'],'keyup_to_planner_margin':planner['terminal_observed_ns']-release['observed_ns'] if release else None}}
(root/'AUDITOR/audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(not all(checks.values()))
