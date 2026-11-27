import hashlib,json,pathlib,re,sys
packet=pathlib.Path(sys.argv[1]); base=pathlib.Path(sys.argv[2]); source=pathlib.Path(sys.argv[3])
result=json.loads((packet/'raw/output/result.json').read_text()); cleanup=json.loads((packet/'raw/output/resource-cleanup.json').read_text()); setup=json.loads((packet/'raw/output/container-setup.json').read_text()); trace=json.loads((packet/'raw/output/early-poll-trace.json').read_text()); freeze=json.loads((packet/'SOURCE-FREEZE.json').read_text())
checks={}
def check(name, value): checks[name]=bool(value)
cancel=result['cancel']; operation=cancel['cancellation']; admission=operation['admitted_monotonic_ns']; release=operation['result']['owner_release_attempt']['release']; independent=result['independent_release_readback']; horizon=result['late_request_horizon_readback']; old=result['independent_task_oracle']; fresh=result['fresh_session_recovery']; polls=trace['polls'];
release_ms=(release['readback_monotonic_ns']-admission)/1e6
readback_ms=(independent['observed_ns']-admission)/1e6
check('test_body_exit_zero',(packet/'raw/output/test-exit-code.txt').read_text().strip()=='0')
check('blocked_release_report_present',result.get('status')=='OBSERVED_SCOPED_XVFB_STANDARD_CALLER_CANCEL_CLEANUP_UNKNOWN')
check('target_generation_observed_and_minted',result['observation']['status']=='observed' and bool(re.fullmatch(r'[0-9a-f]{64}',result['observation']['pointer_binding']['process_generation'])) and bool(re.fullmatch(r'[0-9a-f]{64}',result['observation']['pointer_binding']['window_generation'])) and result['mint']['status']=='minted')
check('real_blocked_owner_sync_entered',result['blocked_owner_sync']['call']=='python-xlib Display.sync')
check('initial_effect_observed_before_cancel',result['input_before_cancel']['synthetic_effect_committed'] is True and result['input_before_cancel']['keys_down']['a'] is True)
check('cancel_response_under_3000ms',0<=result['cancel_elapsed_ms']<3000)
check('exactly_two_forced_early_false_polls',trace['forced_early_timeout_count']==2 and len(polls)>=3 and all(p['forced_early_timeout'] and p['returned'] is False for p in polls[:2]))
check('poll_retried_and_received_real_pipe_response',polls[2]['forced_early_timeout'] is False and polls[2]['returned'] is True and polls[2]['requested_timeout_s']>0)
check('trace_belongs_to_same_cancel_operation',trace['operation_id']==operation['operation_id'])
check('owner_release_receipt_verified',operation['result']['owner_release_attempt']['status']=='readback_verified' and release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[])
check('owner_release_within_4000ms',0<=release_ms<=4000)
check('independent_readback_all_up_within_5000ms',all(v is False for v in independent['keys_down'].values()) and 0<=readback_ms<=5000)
check('delayed_horizon_at_least_8500ms_all_up',horizon['ms_after_cancel_start']>=8500 and all(v is False for v in horizon['keys_down'].values()) and horizon['late_keypress_b_observed'] is False)
check('old_task_oracle_pass',old['status']=='pass' and old['task_success'] is True and old['expected_effect']==[1] and old['measurements']['final_effect']==[1] and old['measurements']['final_effect_count']==[1])
check('fresh_task_oracle_pass',fresh['effect_count_oracle']['status']=='pass' and fresh['effect_count_oracle']['task_success'] is True and fresh['effect_before_input']==[0] and fresh['effect_after_input']==[3] and fresh['effect_at_horizon']==[3])
check('public_old_call_remains_unknown_and_no_replay',cancel['cleanup_status']=='UNKNOWN' and cancel['release_confirmed'] is False and cancel['replay_allowed'] is False and cancel['task_success'] is None and cancel['late_server_request_possible'] is True)
check('final_independent_key_state_all_up',all(v is False for v in result['final_cleanup']['keys_down'].values()))
check('exact_container_image_session_cleanup',cleanup['deleted'] is True and cleanup['imageDeleted'] is True and cleanup['terminated'] is True and cleanup['failure'] is None)
check('test_container_exit_zero',setup['returncode']==0 and cleanup['exit']==0)
check('runtime_result_capture_present',(base/'output/result.json').is_file())
check('vhdx_retained_nonempty',(base/'session-storage-s43/storage.vhdx').is_file() and (base/'session-storage-s43/storage.vhdx').stat().st_size>0)
for rel,expected in freeze['source_files'].items(): check('source_sha_'+rel.replace('/','_'),hashlib.sha256((source/rel).read_bytes()).hexdigest()==expected)
for rel,expected in freeze['runner_files'].items(): check('runner_sha_'+rel,hashlib.sha256((packet/'runner'/rel).read_bytes()).hexdigest()==expected)
failed=[k for k,v in checks.items() if not v]
report={'schema':'agent-interface/wslc-s43-early-poll-independent-audit-v1','attempt_id':freeze['attempt_id'],'checks':checks,'passed':sum(checks.values()),'total':len(checks),'failed':failed,'decision':'PASS_SCOPED' if not failed else 'FAIL','metrics':{'forced_early_false_polls':trace['forced_early_timeout_count'],'poll_retries_until_pipe_response':len(polls),'cancel_response_ms':result['cancel_elapsed_ms'],'owner_release_readback_ms_after_admission':release_ms,'independent_all_up_readback_ms_after_admission':readback_ms,'delayed_request_horizon_ms':horizon['ms_after_cancel_start']},'limitations':['synthetic private Xvfb only','early poll timeouts injected by a test shim; not native Windows kernel pipe timing','public old-call result remains UNKNOWN/replay denied/task_success=null','not physical GUI/MAP01, efficiency, or reliability estimate']}
(packet/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n'); print(json.dumps(report,sort_keys=True,indent=2)); sys.exit(0 if not failed else 1)
