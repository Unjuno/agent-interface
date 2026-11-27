from __future__ import annotations
import datetime,hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
read=lambda p:(root/p).read_bytes()
load=lambda p:json.loads(read(p))
sha=lambda b:hashlib.sha256(b).hexdigest()
c=load('CONDITIONS.json');p=load('PREREGISTRATION.json');r=load('output/result.json')
repo=root.parents[2];checks={}
def check(k,v):checks[k]=bool(v)
def filehash(path):return hashlib.sha256(path.read_bytes()).hexdigest()
check('conditions_hash_pinned_before_run',sha(read('CONDITIONS.json'))==p['conditions_sha256'])
check('source_commit_is_current_main_freeze',c['source_commit']==c['source_remote_main']=='058ab3c36092d5883d15bf44c7f0d4c573d2e763')
check('public_test_source_hash_matches',filehash(repo/'runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py')==c['source_hashes']['test'])
check('xres_identity_source_hash_matches',filehash(repo/'runtime/guarded_x11_v1/process_identity.py')==c['source_hashes']['xres'])
check('runner_hash_matches',sha(read('run-container.py'))==c['source_hashes']['runner'])
check('pinned_harness_binary_hash_matches',filehash(root.parent/'wslc_standard_caller_xvfb_20261025_r23/harness/bin/Release/net9.0-windows10.0.26100.0/S13.exe')==c['source_hashes']['harness'])
check('pinned_stage_manifest_hash_matches',filehash(root.parent/'wslc_standard_caller_xvfb_20261025_r23/STAGE-MANIFEST.json')==c['source_hashes']['stage_manifest'])
check('input_free_identity_preflight_passed',read('output/preflight-status.txt').decode().strip()=='pass' and 'local_xres_identity=' in read('output/xvfb-process-identity-preflight.txt').decode())
check('test_started_after_preflight',read('output/trial-started.txt').decode().startswith('test body starts only after'))
check('exact_requested_2950ms_pause_resumed_by_pidfd',r['xvfb_server_pause']['requested_pause_ms']==2950 and r['xvfb_server_pause']['observed_pause_ms']>=2950 and r['xvfb_server_pause']['signal_identity']=='retained_pidfd' and r['xvfb_server_pause']['resume_receipt']['error'] is None)
can=r['cancel']['cancellation']; rel=r['cancel']['owner_release_attempt'];deadline=can['transaction_deadline_monotonic_ns'];resume=r['xvfb_server_pause']['resume_receipt']['monotonic_ns'];completed=can['completed_monotonic_ns']
check('exact_three_second_transaction_window',deadline-can['admitted_monotonic_ns']==3_000_000_000)
check('server_resumed_before_deadline',resume<deadline)
check('release_worker_expired_at_transaction_deadline',rel['status']=='unknown' and rel['reason']=='transaction_deadline' and can['result']['owner_client_disconnect']['reason']=='transaction_deadline')
check('completion_receipt_arrived_after_deadline',completed>deadline)
check('deadline_failure_is_the_asserted_test_failure',load('output/test-exit-code.txt')==1 and b"AssertionError: 'unknown' != 'disconnected'" in read('output/runner.stderr.txt') and b'FAILED (failures=1)' in read('output/runner.stderr.txt'))
check('caller_preserved_unknown_and_replay_fence',r['cancel']['cleanup_status']=='UNKNOWN' and r['cancel']['release_confirmed'] is False and r['cancel']['replay_allowed'] is False and r['cancel']['task_success'] is None)
check('no_task_or_independent_success_oracle_claimed',r.get('independent_task_oracle') is None and r.get('fresh_session_recovery') is None and r.get('independent_release_readback') is None and r.get('late_request_horizon_readback') is None)
check('test_final_cleanup_observed_all_keys_up',r['final_cleanup']['keys_down']=={'a':False,'b':False,'c':False})
check('harness_exit_one_matches_preserved_test_failure',read('HARNESS-EXIT-CODE.txt').decode().strip()=='1' and load('output/container-setup.json')['returncode']==1)
rows=[json.loads(x) for x in read('HARNESS-INVOCATION.log').decode('utf-8-sig').splitlines() if x.strip()];stages={x.get('stage'):x.get('details',{}) for x in rows}
check('exact_owned_container_deleted',stages.get('container_deleted',{}).get('containerId')==stages.get('container_created',{}).get('containerId'))
check('exact_pinned_image_deleted',stages.get('image_deleted',{}).get('image')==c['image'])
check('exact_session_terminated',stages.get('session_terminated',{}).get('sessionName')==c['session_name'])
check('exact_storage_removed_only_after_termination',stages.get('session_storage_removed',{}).get('storagePath')==c['session_storage_path'] and stages.get('session_storage_removed',{}).get('existsAfter') is False and not pathlib.Path(c['session_storage_path']).exists())
man=load('output/session-storage-manifest.json')
check('single_vhdx_hash_manifest_retained',len(man['files'])==1 and man['files'][0]['path']=='storage.vhdx' and len(man['files'][0]['sha256'])==64 and man['files'][0]['bytes']>0)
classification='COUNTEREXAMPLE_SCOPED_TRANSACTION_DEADLINE' if all(checks.values()) else 'FAIL_OR_UNKNOWN'
report={'schema':'wslc-standard-caller-xvfb-r29-audit-v1','attempt_id':c['attempt_id'],'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'checks':checks,'counts':{'passed':sum(checks.values()),'total':len(checks)},'observations':{'pause_ms':r['xvfb_server_pause']['observed_pause_ms'],'cancel_response_ms':r['cancel_elapsed_ms'],'resume_before_deadline_ms':(deadline-resume)/1e6,'release_worker_status':rel['status'],'release_worker_reason':rel.get('reason'),'completion_after_deadline_ms':(completed-deadline)/1e6,'test_exit_code':load('output/test-exit-code.txt'),'harness_exit_code':int(read('HARNESS-EXIT-CODE.txt').decode().strip()),'final_cleanup_keys_up':r['final_cleanup']['keys_down'],'task_success':None,'runtime_cleanup_status':r['cancel']['cleanup_status']},'limitations':['one synthetic private-Xvfb WSLc boundary trial','independent release readback and old/fresh task oracles did not run after the deadline assertion','does not establish Windows desktop/MAP01 behavior, efficiency or broad reliability','runtime custody remains UNKNOWN; replay denied'],'raw_inputs':['CONDITIONS.json','PREREGISTRATION.json','output/result.json','output/runner.stderr.txt','HARNESS-INVOCATION.log','output/session-storage-manifest.json']}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True));sys.exit(0 if classification.startswith('COUNTEREXAMPLE_') else 1)
