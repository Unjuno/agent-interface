from __future__ import annotations
import datetime, hashlib, json, pathlib, subprocess, sys
root=pathlib.Path(__file__).resolve().parent
repo=root.parents[2]
load=lambda p: json.loads((root/p).read_text(encoding='utf-8-sig'))
pre=load('PREREGISTRATION.json'); cond=load('CONDITIONS.json'); result=load('output/result.json'); invocation=load('INVOCATION-METADATA.json')
checks={}
def check(name, value): checks[name]=bool(value)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
check('attempt_and_source_pin_match', pre['attempt_id']==cond['attempt_id']==invocation['attempt_id'] and pre['source_commit']==cond['source_commit']=='e4e34a163e1f288d8841d300ae719abcf9e58223')
check('checked_out_source_commit_matches', subprocess.run(['git','rev-parse','HEAD'],cwd=repo,capture_output=True,text=True).stdout.strip()==pre['source_commit'])
for rel,digest in pre['source_hashes'].items(): check('source_hash_'+rel.replace('/','_'),sha(repo/rel)==digest)
check('pinned_image_digest_verified',pre['image'] in (root/'output/pinned-image-inspect.txt').read_text() and pre['image'] in invocation['image_info'])
check('network_and_resource_limits', ' none ' in (root/'output/container-state-before-cleanup.txt').read_text() and '2147483648' in (root/'output/container-state-before-cleanup.txt').read_text() and '2000000000' in (root/'output/container-state-before-cleanup.txt').read_text() and '128' in (root/'output/container-state-before-cleanup.txt').read_text())
mounts=(root/'output/container-mounts-before-cleanup.txt').read_text().splitlines()
check('source_mounts_read_only_output_rw', all(f'{p}:readonly=true' in mounts for p in ['/repo','/deps','/stage','/xkb']) and '/out:readonly=false' in mounts)
check('tmpfs_exec_enabled', 'rw,exec,nosuid,nodev,mode=1777,size=512m' in (root/'output/container-state-before-cleanup.txt').read_text())
check('container_exit_and_cleanup', ' exited 0 ' in (root/'output/container-state-before-cleanup.txt').read_text() and (root/'output/docker-cleanup-exit-code.txt').read_text().strip()=='0' and 'no such object' in (root/'output/container-absent-after-cleanup.txt').read_text().lower())
check('runner_and_harness_exit_zero', (root/'output/docker-run-exit-code.txt').read_text().strip()=='0' and (root/'output/test-exit-code.txt').read_text().strip()=='0' and load('output/container-setup.json').get('returncode')==0)
check('preflight_passed_before_test', (root/'output/preflight-status.txt').read_text().strip()=='pass' and 'local_xres_identity=' in (root/'output/xvfb-process-identity-preflight.txt').read_text())
check('source_stage_and_xkb_hashes', sha(repo/'runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py')==pre['source_hashes']['runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py'] and sha(root.parent/'wslc_standard_caller_xvfb_20261025_r34'/'xkb-materialization.json')==pre['xkb_manifest_sha256'])
# Verify every file in the reused stage and locally materialized XKB tree against captured manifests.
stage_rows=json.loads((repo/'research/integration/wslc_standard_caller_xvfb_20261025_r33/STAGE-MANIFEST.json').read_text(encoding='utf-8-sig'))
stage_root=repo/'research/integration/wslc_standard_caller_xvfb_20261025_r16/stage'
check('stage_manifest_all_files_match',len(stage_rows)==1252 and all(sha(stage_root/row['path'])==row['sha256'] for row in stage_rows))
xkb=json.loads((root.parent/'wslc_standard_caller_xvfb_20261025_r34/xkb-materialization.json').read_text())
xkb_root=root.parent/'wslc_standard_caller_xvfb_20261025_r34/xkb-materialized'
check('xkb_materialization_all_files_match',xkb['files']==293 and all(sha(xkb_root/row['path'])==row['sha256'] for row in xkb['manifest']))
check('requested_pause_pidfd_resume',result['xvfb_server_pause']['requested_pause_ms']==3500 and result['xvfb_server_pause']['observed_pause_ms']>=3500 and result['xvfb_server_pause']['signal_identity']=='retained_pidfd' and result['xvfb_server_pause']['resume_receipt']['error'] is None)
cancel=result['cancel']; tx=cancel['cancellation']; deadline=tx['transaction_deadline_monotonic_ns']; start=tx['admitted_monotonic_ns']; released=result['independent_release_readback']['owner_release_attempt']['release']['readback_monotonic_ns']
check('public_cancel_under_bound',result['cancel_elapsed_ms']<3000)
check('exact_four_second_transaction',deadline-start==4_000_000_000)
check('release_readback_before_deadline',result['independent_release_readback']['owner_release_attempt']['status']=='readback_verified' and result['independent_release_readback']['owner_release_attempt']['release']['verified'] is True and released<=deadline)
check('independent_release_readback_under_five_seconds',(result['independent_release_readback']['observed_ns']-result['timing_ns']['cancel_started'])/1e6<=5000 and result['independent_release_readback']['keys_down']=={'a':False,'b':False})
horizon=result['late_request_horizon_readback']
check('late_event_horizon_clear',horizon['ms_after_cancel_start']>=8500 and horizon['late_keypress_b_observed'] is False and horizon['keys_down']=={'a':False,'b':False,'c':False})
old=result['independent_task_oracle']; fresh=result['fresh_session_recovery']['task_oracle']
check('old_task_oracle_pass',result['counted_task_outcomes']['old_task']=='pass' and old['status']=='pass' and all(old['checks'].values()))
check('fresh_task_exact_once_pass',result['counted_task_outcomes']['fresh_task']=='pass' and fresh['status']=='pass' and fresh['task_success'] is True and all(fresh['checks'].values()) and result['fresh_session_recovery']['effect_count_before_input']==[0] and result['fresh_session_recovery']['effect_count_after_input']==[1] and result['fresh_session_recovery']['effect_count_at_horizon']==[1])
check('old_unknown_fence_unchanged',fresh['checks']['old_unknown_fence_preserved'] and fresh['checks']['old_fence_unchanged_after_fresh_task'] and result['fresh_session_recovery']['old_cancellation_fence']['cleanup_status']=='UNKNOWN' and result['fresh_session_recovery']['old_cancellation_fence']['replay_allowed'] is False)
check('runtime_unknown_replay_denied_task_success_null',cancel['cleanup_status']=='UNKNOWN' and cancel['release_confirmed'] is False and cancel['replay_allowed'] is False and cancel['task_success'] is None and fresh['runtime_task_success'] is None)
check('xvfb_stopped', (root/'output/xvfb-process-absent-after-run.txt').read_text().strip().lower()=='true')
margin=(deadline-released)/1e6
raw=[]
for path in sorted(root.rglob('*')):
    if path.is_file() and path.name not in {'AUDIT.json','AUDIT-EXECUTION.log'}:
        raw.append({'path':path.relative_to(repo).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
classification='PASS_SCOPED_4S_TRANSACTION_3500MS' if all(checks.values()) else 'STOP_OR_FAIL'
report={'schema':'wslc-standard-caller-xvfb-r37-audit-v1','attempt_id':pre['attempt_id'],'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'checks':checks,'counts':{'passed':sum(checks.values()),'total':len(checks)},'observations':{'requested_pause_ms':result['xvfb_server_pause']['requested_pause_ms'],'observed_pause_ms':result['xvfb_server_pause']['observed_pause_ms'],'cancel_response_ms':result['cancel_elapsed_ms'],'transaction_elapsed_ms':(tx['completed_monotonic_ns']-start)/1e6,'release_deadline_margin_ms':margin,'independent_release_readback_ms_after_cancel_start':(result['independent_release_readback']['observed_ns']-result['timing_ns']['cancel_started'])/1e6,'late_horizon_ms':horizon['ms_after_cancel_start'],'old_task':'pass','fresh_task':'pass','fresh_input_invocation_to_effect_readback_completed_ms':result['fresh_session_recovery']['effect_timing_ms']['input_invocation_to_effect_readback_completed'],'runtime_cleanup_status':cancel['cleanup_status'],'runtime_task_success':cancel['task_success'],'container_removed':True},'limitations':['single synthetic Xvfb container run','not Windows desktop, MAP01, or a real application','runtime cancellation remains UNKNOWN and replay denied','one result is not a reliability or efficiency estimate'],'raw_files':raw}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'classification':classification,'counts':report['counts'],'failed_checks':[k for k,v in checks.items() if not v],'observations':report['observations']},indent=2))
sys.exit(0 if classification.startswith('PASS_') else 1)