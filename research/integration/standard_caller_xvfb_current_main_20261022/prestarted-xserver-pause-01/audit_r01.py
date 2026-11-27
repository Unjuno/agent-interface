from pathlib import Path
import hashlib,json,subprocess,sys

repo=Path.cwd(); base=repo/'research/integration/standard_caller_xvfb_current_main_20261022/prestarted-xserver-pause-01'; raw=base/'raw'
conditions=json.loads((base/'conditions.json').read_text(encoding='utf-8'))
result=json.loads((raw/'result.json').read_text(encoding='utf-8'))
identity=json.loads((raw/'source-identity.json').read_text(encoding='utf-8'))
raw_checks=[]
for line in (raw/'SHA256SUMS.txt').read_text().splitlines():
 expected,relative=line.split('  ',1); path=raw/relative
 actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
 raw_checks.append({'path':relative,'expected_sha256':expected,'actual_sha256':actual,'match':actual==expected})
source_checks=[]
for line in (raw/'candidate-runtime-manifest.sha256').read_text().splitlines():
 expected,name=line.split('  ',1); actual=hashlib.sha256((repo/name).read_bytes()).hexdigest()
 source_checks.append({'path':name,'expected_sha256':expected,'actual_sha256':actual,'match':expected==actual})
server=result['xvfb_server_pause']; response=result['cancel_response']; cancellation=response['cancellation']
admitted=cancellation['admitted_monotonic_ns']; returned=result['timing_ns']['cancel_returned']; call_started=result['timing_ns']['cancel_started']; resumed=server['resumed']['monotonic_ns']; stopped=server['stopped_monotonic_ns']
release_ns=result['cancel']['owner_release_attempt']['release']['readback_monotonic_ns']; parent_ns=result['independent_release_readback']['observed_ns']; terminal_ns=result['cancellation_terminal']['completed_monotonic_ns']
horizon=result['late_request_horizon_readback']; fresh=result['fresh_session_recovery']; old=result['cancel']
checks={
 'baseline_and_candidate_identity_match_frozen_conditions':identity['baseline_main']==conditions['baseline_main'] and identity['candidate_commit']==conditions['candidate_commit'],
 'only_test_harness_changed_from_baseline':identity['changed_paths']==conditions['source_changed_paths'],
 'all_candidate_source_hashes_match':len(source_checks)==5 and all(x['match'] for x in source_checks),
 'all_raw_hashes_match':bool(raw_checks) and all(x['match'] for x in raw_checks),
 'test_exited_zero':(raw/'exit-code.txt').read_text().strip()=='0' and 'Ran 1 test' in (raw/'stderr.txt').read_text() and 'OK' in (raw/'stderr.txt').read_text(),
 'xvfb_exited_zero':(raw/'xvfb-exit-code.txt').read_text().strip()=='0',
 'xvfb_cleanup_confirmed':'No Xvfb process matched' in (raw/'xvfb-process-check.txt').read_text(),
 'private_socket_namespace_ready':'1777 root:root /tmp/.X11-unix' in (raw/'private-socket-dir.txt').read_text(),
 'xvfb_pause_timer_resumed_without_error':server['requested_pause_ms']==conditions['frozen']['pause_ms'] and server['resumed']['error'] is None and resumed is not None,
 'xvfb_process_pause_duration_within_bound':1000 <= server['observed_pause_ms'] <= 2500,
 'caller_returned_while_xvfb_still_paused':returned < resumed,
 'admission_to_response_within_300ms':(returned-admitted)/1e6 <= conditions['frozen']['caller_response_target_ms'],
 'pending_response_kept_unknown_fence':response['status']=='pending' and response['release_confirmed'] is False and response['cleanup_status']=='UNKNOWN' and response['task_success'] is None and response['replay_allowed'] is False,
 'release_readback_completed_after_server_resumed':release_ns >= resumed and result['cancel']['owner_release_attempt']['status']=='readback_verified',
 'independent_release_readback_all_up':all(v is False for v in result['independent_release_readback']['keys_down'].values()),
 'release_readback_within_100ms_after_resume':(parent_ns-resumed)/1e6 <= 150,
 'terminal_within_5s_from_admission':(terminal_ns-admitted)/1e6 <= 5000,
 'late_horizon_all_up_and_no_delayed_old_press':all(v is False for v in horizon['keys_down'].values()) and horizon['late_keypress_b_observed'] is False,
 'fresh_generation_distinct_and_task_oracle_pass':fresh['new_target_xid']!=result['observation']['pointer_binding']['surface'] and fresh['new_session_id']!=cancellation['owner_generation']['session_id'] and fresh['task_oracle']['status']=='pass' and fresh['task_oracle']['task_success'] is True,
 'old_cancellation_remained_unknown_and_replay_denied':old['cleanup_status']=='UNKNOWN' and old['release_confirmed'] is False and old['task_success'] is None and old['replay_allowed'] is False and old['late_server_request_possible'] is True,
}
overall='PASS_SCOPED_PAUSE_WITHIN_ADMISSION_BUDGET_AND_POST_RESUME_RECOVERY' if all(checks.values()) else 'HOLD_AUDIT_MISMATCH'
report={'schema':'agent-interface/xvfb-server-pause-audit-v1','run_id':conditions['run_id'],'baseline_main':conditions['baseline_main'],'candidate_commit':conditions['candidate_commit'],'candidate_test_commit':conditions['candidate_commit'],'raw_file_count':len(raw_checks),'raw_hashes_match':checks['all_raw_hashes_match'],'source_hashes':source_checks,'checks':checks,'timings_ms':{'admission_to_response':(returned-admitted)/1e6,'test_call_start_to_response':(returned-call_started)/1e6,'pre_admission_harness_overhead':(admitted-call_started)/1e6,'xvfb_pause_observed':server['observed_pause_ms'],'xvfb_resume_to_supervisor_release_readback':(release_ns-resumed)/1e6,'xvfb_resume_to_independent_parent_readback':(parent_ns-resumed)/1e6,'admission_to_terminal':(terminal_ns-admitted)/1e6,'cancel_start_to_delayed_request_horizon':horizon['ms_after_cancel_start']},'runtime_fence':{'status':old['cleanup_status'],'release_confirmed':old['release_confirmed'],'task_success':old['task_success'],'replay_allowed':old['replay_allowed'],'late_server_request_possible':old['late_server_request_possible']},'fresh_task_oracle':fresh['task_oracle'],'wrapper_status':'not captured by the initial execution-tool response; candidate and Xvfb exit codes are preserved; candidate was not retried','limitations':['one 1.5 s stopped-process schedule, not reliability','test-only SIGSTOP of private Xvfb; no host-wide I/O or physical input','release occurs after X server resumes; no release is claimed while X server is stopped','fresh task oracle is synthetic and runtime task_success remains null','no physical GUI/MAP01, matched efficiency, or WSLc portability'] ,'overall':overall}
encoded=json.dumps(report,indent=2,sort_keys=True)+'\n'
path=base/'audit.json'
if '--write' in sys.argv: path.write_text(encoded,encoding='utf-8')
else:
 saved=json.loads(path.read_text(encoding='utf-8'))
 if saved != report: raise SystemExit('saved audit differs from recomputed read-only audit')
print(encoded,end='')
if not all(checks.values()): raise SystemExit(1)