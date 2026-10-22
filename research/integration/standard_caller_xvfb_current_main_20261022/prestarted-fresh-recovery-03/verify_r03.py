from pathlib import Path
import hashlib,json,subprocess
repo=Path.cwd(); base=repo/'research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-03'; raw=base/'raw'
conditions=json.loads((base/'conditions.json').read_text()); result=json.loads((raw/'result.json').read_text())
raw_checks=[]
for line in (raw/'SHA256SUMS.txt').read_text().splitlines():
 expected,relative=line.split(None,1); relative=relative.lstrip('*'); path=raw/relative
 actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
 raw_checks.append({'path':relative,'expected_sha256':expected,'actual_sha256':actual,'match':actual==expected})
source=[]
for line in (raw/'runtime-manifest.sha256').read_text().splitlines():
 expected,path=line.split(); actual=hashlib.sha256((repo/path).read_bytes()).hexdigest(); source.append({'path':path,'expected_sha256':expected,'actual_sha256':actual,'match':expected==actual})
main=subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip(); source_commit=conditions['source']['commit']; host_source=json.loads((raw/'host-source.json').read_text())
ancestor=subprocess.run(['git','merge-base','--is-ancestor',source_commit,main]).returncode==0
runtime_diff=subprocess.run(['git','diff','--quiet',source_commit,main,'--','runtime/cli_v1','runtime/guarded_x11_v1','runtime/backends/x11_v1']).returncode==0
admitted=result['cancel_response']['cancellation']['admitted_monotonic_ns']; response=result['timing_ns']['cancel_returned']; terminal=result['cancel']['cancellation']['completed_monotonic_ns']; canceled=result['cancel']['cancellation']['result']; release=canceled['owner_release_attempt']['release']['readback_monotonic_ns']; parent=result['independent_release_readback']['observed_ns']; horizon=result['late_request_horizon_readback']; fresh=result['fresh_session_recovery']
raw_exit=(raw/'exit-code.txt').read_text().strip(); xvfb_exit=(raw/'xvfb-exit-code.txt').read_text().strip(); wrapper_exit=(raw/'runner-exit-code.txt').read_text().strip(); wrapper_log=(raw/'runner.log').read_text(errors='replace')
checks={
 'all_raw_hashes_match':bool(raw_checks) and all(x['match'] for x in raw_checks),
 'host_verified_source_was_current_main':host_source['origin_main']==source_commit and host_source['worktree_head']==source_commit,'run_source_is_current_main_ancestor':ancestor,'no_relevant_runtime_diff_since_run_source':runtime_diff,
 'all_five_source_hashes_match':len(source)==5 and all(x['match'] for x in source),
 'xvfb_ready_in_private_mode_1777_socket_namespace':'1777 root:root /tmp/.X11-unix' in (raw/'private-socket-dir.txt').read_text(),
 'candidate_unittest_passed':raw_exit=='0' and 'Ran 1 test' in (raw/'stderr.txt').read_text() and 'OK' in (raw/'stderr.txt').read_text(),
 'xvfb_exited_zero':xvfb_exit=='0','wrapper_error_preserved_and_not_misclassified':wrapper_exit=='2' and 'numeric argument required' in wrapper_log,
 'no_xvfb_process_remained':'No Xvfb process matched' in (raw/'xvfb-process-check.txt').read_text(),
 'caller_response_within_300ms':(response-admitted)/1e6<=conditions['frozen_conditions']['independent_research_cancel_target_ms'],
 'independent_release_readback_all_up':all(v is False for v in result['independent_release_readback']['keys_down'].values()),
 'late_horizon_all_up_and_no_old_press':all(v is False for v in horizon['keys_down'].values()) and horizon['late_keypress_b_observed'] is False,
 'fresh_target_session_generation_distinct':fresh['new_target_xid']!=result['observation']['pointer_binding']['surface'] and fresh['new_session_id']!=result['cancel_response']['cancellation']['owner_generation']['session_id'] and fresh['new_process_generation']!=result['observation']['process_generation'],
 'fresh_synthetic_task_oracle_pass':fresh['task_oracle']['status']=='pass' and fresh['task_oracle']['task_success'] is True and fresh['task_oracle']['runtime_task_success'] is None,
 'old_unknown_fence_remains_denied':canceled['cleanup_status']=='UNKNOWN' and canceled['late_server_request_possible'] is True and canceled['release_confirmed'] is False and canceled['task_success'] is None and canceled['replay_allowed'] is False,
}
report={'schema':'agent-interface/r03-xvfb-evidence-audit-v1','run_id':conditions['run_id'],'run_source':source_commit,'audited_main_at_run':source_commit,'current_main_at_audit':main,'host_source_receipt':host_source,'raw_file_count':len(raw_checks),'raw_hashes_match':checks['all_raw_hashes_match'],'source_hashes':source,'timings_ms':{'admission_to_response':(response-admitted)/1e6,'admission_to_terminal':(terminal-admitted)/1e6,'admission_to_supervisor_readback':(release-admitted)/1e6,'admission_to_parent_readback':(parent-admitted)/1e6,'cancel_start_to_horizon':horizon['ms_after_cancel_start']},'fresh_session':{'old_target_xid':result['observation']['pointer_binding']['surface'],'new_target_xid':fresh['new_target_xid'],'old_session_id':result['cancel_response']['cancellation']['owner_generation']['session_id'],'new_session_id':fresh['new_session_id'],'old_generation':result['observation']['process_generation'],'new_generation':fresh['new_process_generation'],'oracle_status':fresh['task_oracle']['status'],'synthetic_task_success':fresh['task_oracle']['task_success'],'runtime_task_success':fresh['task_oracle']['runtime_task_success']},'old_cancel':{'cleanup_status':canceled['cleanup_status'],'late_server_request_possible':canceled['late_server_request_possible'],'release_confirmed':canceled['release_confirmed'],'task_success':canceled['task_success'],'replay_allowed':canceled['replay_allowed']},'test_exit_code':raw_exit,'xvfb_exit_code':xvfb_exit,'wrapper_exit_code':wrapper_exit,'checks':checks,'overall':'PASS_SCOPED_REPEAT_WITH_WRAPPER_ERROR' if all(checks.values()) else 'HOLD_AUDIT_MISMATCH','limitations':['second observed trial only; not a reliability estimate','owner blocked in Display.sync while X server served supervisor','whole-X-server unavailability not tested','synthetic task oracle; no physical GUI/MAP01','no matched efficiency','no WSLc allocation']}
(base/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps(report,indent=2,sort_keys=True))
if not all(checks.values()): raise SystemExit(1)
