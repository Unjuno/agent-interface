from __future__ import annotations
import hashlib, json, pathlib, subprocess, sys
root=pathlib.Path(__file__).resolve().parent
read=lambda p: (root/p).read_bytes()
load=lambda p: json.loads(read(p))
conditions=load('CONDITIONS.json'); prereg=load('PREREGISTRATION.json'); result=load('output/result.json')
checks={}
def check(name, ok): checks[name]=bool(ok)
def sha(p): return hashlib.sha256(read(p)).hexdigest()
repo=root.parents[2]
check('condition_hash_matches_preregistration', sha('CONDITIONS.json') == prereg['conditions_sha256'])
check('source_commit_and_parent_pinned', conditions['source_commit'] == 'aaa4fce67440fcd475e71e3134345f5649336f39' and conditions['source_base_commit'] == conditions['source_remote_main'] == '058ab3c36092d5883d15bf44c7f0d4c573d2e763')
check('checked_out_commit_matches_preregistration', subprocess.run(['git','rev-parse','HEAD'],cwd=repo,capture_output=True,text=True).stdout.strip() == conditions['source_commit'])
check('test_source_hash_matches', hashlib.sha256((repo/'runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py').read_bytes()).hexdigest() == conditions['source_hashes']['test'])
check('XRes_source_hash_matches', hashlib.sha256((repo/'runtime/guarded_x11_v1/process_identity.py').read_bytes()).hexdigest() == conditions['source_hashes']['xres'])
check('mcp_server_timeout_source_hash_matches', hashlib.sha256((repo/'runtime/cli_v1/mcp_server.py').read_bytes()).hexdigest() == conditions['source_hashes']['mcp_server'])
check('delayed_release_regression_source_hash_matches', hashlib.sha256((repo/'runtime/cli_v1/test_mcp_owned_process.py').read_bytes()).hexdigest() == conditions['source_hashes']['regression_test'])
check('parameterized_runner_hash_matches', sha('run-container.py') == conditions['source_hashes']['runner'])
check('comparison_packet_readme_hash_matches', hashlib.sha256((root.parents[2]/'research/integration/x11_queued_up_cancel_20261023_r01/README.md').read_bytes()).hexdigest() == conditions['source_hashes']['comparison_packet_readme'])
check('supervisor_release_before_transaction_deadline', conditions['bounds']['supervisor_release_before_transaction_deadline'] is True and result['cancel']['owner_release_attempt']['status'] == 'readback_verified' and result['cancel']['owner_release_attempt']['release']['readback_monotonic_ns'] <= result['cancel_response']['cancellation']['transaction_deadline_monotonic_ns'])
check('runner_binary_hash_matches', hashlib.sha256((root.parent/'wslc_standard_caller_xvfb_20261025_r23/harness/bin/Release/net9.0-windows10.0.26100.0/S13.exe').read_bytes()).hexdigest() == conditions['source_hashes']['harness'])
check('stage_manifest_hash_matches', hashlib.sha256((root.parent/'wslc_standard_caller_xvfb_20261025_r23/STAGE-MANIFEST.json').read_bytes()).hexdigest() == conditions['source_hashes']['stage_manifest'])
check('harness_exit_zero', read('HARNESS-EXIT-CODE.txt').decode().strip() == '0')
check('container_test_exit_zero', load('output/container-setup.json').get('returncode') == 0)
check('pause_exactly_requested_and_pidfd_resumed', result['xvfb_server_pause']['requested_pause_ms'] == int(conditions['conditions']['AGENT_INTERFACE_MCP_XVFB_SERVER_PAUSE_MS']) and result['xvfb_server_pause']['signal_identity'] == 'retained_pidfd' and result['xvfb_server_pause']['resume_receipt']['error'] is None and result['xvfb_server_pause']['observed_pause_ms'] >= int(conditions['conditions']['AGENT_INTERFACE_MCP_XVFB_SERVER_PAUSE_MS']))
check('cancel_return_under_3s', result['cancel_elapsed_ms'] < 3000)
check('four_second_transaction_budget', result['cancel_response']['cancellation']['transaction_deadline_monotonic_ns'] - result['cancel_response']['cancellation']['admitted_monotonic_ns'] == 4000000000)
check('cancel_unknown_fence_retained', result['cancel']['cleanup_status'] == 'UNKNOWN' and result['cancel']['release_confirmed'] is False and result['cancel']['replay_allowed'] is False and result['cancel']['late_server_request_possible'] is True and result['cancel']['task_success'] is None)
check('independent_release_keys_up', result['independent_release_readback']['keys_down'] == {'a':False,'b':False})
check('delayed_key_absent_at_horizon', result['late_request_horizon_readback']['late_keypress_b_observed'] is False and result['late_request_horizon_readback']['ms_after_cancel_start'] >= 8500 and result['late_request_horizon_readback']['keys_down'] == {'a':False,'b':False,'c':False})
check('old_task_exact_effect_pass', result['independent_task_oracle']['status'] == 'pass' and all(result['independent_task_oracle']['checks'].values()))
check('fresh_task_exact_effect_pass_and_old_fence_preserved', result['fresh_session_recovery']['task_oracle']['status'] == 'pass' and all(result['fresh_session_recovery']['task_oracle']['checks'].values()) and result['fresh_session_recovery']['old_cancellation_fence']['cleanup_status'] == 'UNKNOWN')
check('fresh_task_effect_count_exactly_one', result['fresh_session_recovery']['effect_count_before_input'] == [0] and result['fresh_session_recovery']['effect_count_after_input'] == [1] and result['fresh_session_recovery']['effect_count_at_horizon'] == [1])
check('final_keys_up', result['final_cleanup']['keys_down'] == {'a':False,'b':False,'c':False})
check('Xvfb_absent', read('output/xvfb-process-absent-after-run.txt').decode().strip().lower() == 'true')
log_rows=[json.loads(line) for line in read('HARNESS-INVOCATION.log').decode('utf-8-sig').splitlines() if line.strip()]
stages={row.get('stage'):row.get('details',{}) for row in log_rows}
check('exact_container_deleted', stages.get('container_deleted',{}).get('containerId') == stages.get('container_created',{}).get('containerId'))
check('session_image_deleted', stages.get('image_deleted',{}).get('image') == conditions['image'])
check('exact_session_terminated', stages.get('session_terminated',{}).get('sessionName') == conditions['session_name'])
check('exact_storage_removed_after_termination', stages.get('session_storage_removed',{}).get('storagePath') == conditions['session_storage_path'] and stages.get('session_storage_removed',{}).get('existsAfter') is False and not pathlib.Path(conditions['session_storage_path']).exists())
manifest=load('output/session-storage-manifest.json')
check('storage_manifest_single_file_and_hash', len(manifest['files']) == 1 and manifest['files'][0]['path'] == 'storage.vhdx' and len(manifest['files'][0]['sha256']) == 64 and manifest['files'][0]['bytes'] > 0)
# The immutable pre-registration names cancellation/late-event/task outcomes, but does not explicitly preregister a separate numeric independent-release-readback deadline.
check('preregistered_release_readback_within_5s', conditions['bounds']['independent_release_readback_ms_from_cancel_start'] == 5000 and ((result['independent_release_readback']['observed_ns']-result['timing_ns']['cancel_started'])/1e6) <= conditions['bounds']['independent_release_readback_ms_from_cancel_start'])
check('exact_2950ms_boundary_condition', int(conditions['conditions']['AGENT_INTERFACE_MCP_XVFB_SERVER_PAUSE_MS']) == 2950 and result['xvfb_server_pause']['requested_pause_ms'] == 2950)
check('result_caller_test_exit_zero', load('output/test-exit-code.txt') == 0)
verdict='PASS_SCOPED_4S_TRANSACTION_RECOVERY' if all(checks.values()) else 'FAIL_OR_UNKNOWN'
report={'schema':'wslc-standard-caller-xvfb-r30-audit-v1','attempt_id':conditions['attempt_id'],'audited_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'classification':verdict,'checks':checks,'counts':{'passed':sum(checks.values()),'total':len(checks),'protocol_passed':sum(checks.values()),'protocol_total':len(checks)},'observations':{'cancel_elapsed_ms':result['cancel_elapsed_ms'],'independent_release_readback_ms_after_cancel_start':(result['independent_release_readback']['observed_ns']-result['timing_ns']['cancel_started'])/1e6,'fresh_input_to_effect_readback_ms':result['fresh_session_recovery']['effect_timing_ms']['input_invocation_to_effect_readback_completed'],'late_horizon_ms':result['late_request_horizon_readback']['ms_after_cancel_start'],'release_deadline_margin_ms':(result['cancel_response']['cancellation']['transaction_deadline_monotonic_ns']-result['cancel']['owner_release_attempt']['release']['readback_monotonic_ns'])/1e6,'runtime_cleanup_status':result['cancel']['cleanup_status'],'runtime_task_success':result['fresh_session_recovery']['task_oracle']['runtime_task_success']},'limitations':['synthetic private Xvfb only','not Win32 desktop or MAP01','one patched-branch WSLc 2950ms transaction-budget trial; synthetic Xvfb only; not Windows desktop or MAP01','runtime cancellation custody remains UNKNOWN; replay denied','R30 preregistered independent release readback <=5000 ms; one patched trial cannot establish reliability'],'raw_inputs':['CONDITIONS.json','PREREGISTRATION.json','output/result.json','HARNESS-INVOCATION.log','output/session-storage-manifest.json']}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
sys.exit(0 if verdict.startswith('PASS_') else 1)







