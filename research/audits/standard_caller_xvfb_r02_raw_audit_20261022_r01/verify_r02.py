from pathlib import Path
import hashlib,json,subprocess
repo=Path.cwd(); run=repo/'research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-02'; raw=run/'raw'
conditions=json.loads((raw/'conditions.json').read_text()); result=json.loads((raw/'result.json').read_text())
raw_checks=[]
for line in (raw/'SHA256SUMS.txt').read_text().splitlines():
 expected,name=line.split(None,1); name=name.strip().lstrip('*'); path=raw/name
 actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
 raw_checks.append({'path':name,'expected_sha256':expected,'actual_sha256':actual,'match':actual==expected})
source_checks=[]
for line in (raw/'runtime-manifest.sha256').read_text().splitlines():
 expected,path=line.split(None,1); actual=hashlib.sha256((repo/path).read_bytes()).hexdigest()
 source_checks.append({'path':path,'expected_sha256':expected,'current_sha256':actual,'match':actual==expected})
source=conditions['source']['commit']; current=subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
ancestor=subprocess.run(['git','merge-base','--is-ancestor',source,current]).returncode==0
runtime_diff=subprocess.run(['git','diff','--quiet',source,current,'--','runtime/cli_v1','runtime/guarded_x11_v1','runtime/backends/x11_v1']).returncode==0
admitted=result['cancel_response']['cancellation']['admitted_monotonic_ns']; response=result['timing_ns']['cancel_returned']; terminal=result['cancel']['cancellation']['completed_monotonic_ns']
release=result['cancel']['cancellation']['result']['owner_release_attempt']['release']['readback_monotonic_ns']; parent=result['independent_release_readback']['observed_ns']; horizon=result['late_request_horizon_readback']; fresh=result['fresh_session_recovery']; old=result['cancel']['cancellation']['result']
old_gen=result['cancel_response']['cancellation']['owner_generation']; old_target=result['observation']['pointer_binding']['surface']
new_session=fresh['new_session_id']; new_gen=fresh['new_process_generation']; new_target=fresh['new_target_xid']
checks={
 'all_17_raw_hashes_match':len(raw_checks)==17 and all(x['match'] for x in raw_checks),
 'all_5_runtime_source_hashes_match_current_checkout':len(source_checks)==5 and all(x['match'] for x in source_checks),
 'run_source_is_current_main_ancestor':ancestor,'no_relevant_runtime_diff_since_run_source':runtime_diff,
 'process_exit_zero':(raw/'exit-code.txt').read_text().strip()=='0','xvfb_exit_zero':(raw/'xvfb-exit-code.txt').read_text().strip()=='0',
 'owner_blocked_in_real_display_sync':result['blocked_owner_sync']['call']=='python-xlib Display.sync' and result['input_before_cancel']['owner_sync_return_receipt_present'] is False,
 'caller_returned_pending':result['cancel_response']['status']=='pending' and result['cancel_response']['cancellation']['status']=='pending',
 'caller_response_within_300ms':(response-admitted)/1e6<=conditions['frozen_conditions']['independent_research_cancel_target_ms'],
 'independent_release_readback_all_up':all(v is False for v in result['independent_release_readback']['keys_down'].values()),
 'late_request_horizon_all_up_and_no_delayed_press':all(v is False for v in horizon['keys_down'].values()) and horizon['late_keypress_b_observed'] is False,
 'fresh_target_session_and_generation_are_distinct':new_target!=old_target and new_session!=old_gen['session_id'] and new_gen!=result['observation']['process_generation'],
 'fresh_session_oracle_pass':fresh['task_oracle']['status']=='pass' and fresh['task_oracle']['task_success'] is True and fresh['task_oracle']['runtime_task_success'] is None,
 'old_fence_unchanged':fresh['task_oracle']['checks']['old_fence_unchanged_after_fresh_task'] is True,
 'old_cancel_stays_unknown_and_replay_denied':old['cleanup_status']=='UNKNOWN' and old['late_server_request_possible'] is True and old['release_confirmed'] is False and old['task_success'] is None and old['replay_allowed'] is False,
}
report={'schema':'agent-interface/r02-raw-evidence-audit-v1','run_id':conditions['run_id'],'audit_current_main':current,'run_source':source,'raw_file_count':len(raw_checks),'raw_hashes_match':checks['all_17_raw_hashes_match'],'runtime_source_file_count':len(source_checks),'source_hashes_match_current_checkout':checks['all_5_runtime_source_hashes_match_current_checkout'],'identities':{'old_target_xid':old_target,'new_target_xid':new_target,'old_session_id':old_gen['session_id'],'new_session_id':new_session,'old_process_generation':result['observation']['process_generation'],'new_process_generation':new_gen},'timings_ms':{'caller_admission_to_response':(response-admitted)/1e6,'caller_admission_to_terminal':(terminal-admitted)/1e6,'caller_admission_to_supervisor_release_readback':(release-admitted)/1e6,'caller_admission_to_parent_keymap_readback':(parent-admitted)/1e6,'cancel_start_to_late_request_horizon':horizon['ms_after_cancel_start']},'fresh_session':{'before':fresh['effect_before_input'],'after_input':fresh['effect_after_input'],'at_horizon':fresh['effect_at_horizon'],'oracle_status':fresh['task_oracle']['status'],'synthetic_task_success':fresh['task_oracle']['task_success'],'runtime_task_success':fresh['task_oracle']['runtime_task_success'],'old_fence_unchanged':checks['old_fence_unchanged']},'old_cancel':{'cleanup_status':old['cleanup_status'],'late_server_request_possible':old['late_server_request_possible'],'release_confirmed':old['release_confirmed'],'task_success':old['task_success'],'replay_allowed':old['replay_allowed']},'checks':checks,'overall':'PASS_SCOPED_RAW_AND_SOURCE_AUDIT' if all(checks.values()) else 'HOLD_AUDIT_MISMATCH','limitations':['one private-Xvfb sample only','owner blocked in Display.sync while the X server remained responsive to supervisor','does not prove whole-X-server-unavailable release','synthetic task oracle; not physical GUI or MAP01','not a reliability or matched-efficiency estimate','no WSLc allocation']}
out=repo/'research/audits/standard_caller_xvfb_r02_raw_audit_20261022_r01/audit.json'; out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps(report,indent=2,sort_keys=True))
if not all(checks.values()): raise SystemExit(1)
