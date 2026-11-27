#!/usr/bin/env python3
"""Independent S29 audit. Uses only raw artifacts and Python/Git standard interfaces."""
import datetime, hashlib, json, pathlib, subprocess, sys
packet=pathlib.Path(__file__).resolve().parent; repo=packet.parents[2]; asset=pathlib.Path(sys.argv[1]); out=packet/'output'; xout=asset/'output'; checks={}
def ck(k,v): checks[k]=bool(v)
def j(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
pre=j(packet/'PREREGISTRATION.json'); cor=j(packet/'PREREGISTRATION-CORRECTION-001.json'); ready=j(packet/'INPUT-READINESS-AUDIT.json'); inv=j(packet/'INVOCATION-METADATA.json'); cond=j(packet/'CONDITIONS.json'); result=j(out/'result.json'); cleanup=j(out/'resource-cleanup.json'); post=j(packet/'POST_CLEANUP.json')
head=subprocess.check_output(['git','rev-parse','origin/main'],cwd=repo,text=True).strip(); remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=repo,text=True).split()[0]
ck('attempt_binding',pre['attempt_id']==cor['attempt_id']==inv['attempt_id']==cond['attempt_id']=='wslc-standard-caller-xvfb-20261025-s29-2a75a13919')
ck('corrected_current_main',head==remote==cor['correct_source_commit']==ready['source_commit'] and cor['local_remote_match'])
ck('source_archive_reproducible',cor['archive_match'] and cor['stored_archive_sha256'].lower()==cor['regenerated_archive_sha256'].lower()==sha(asset/'current-main-runtime.tar')==sha(asset/'current-main-runtime-verification.tar'))
for rel,ef,of in [('runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py','extracted_test_git_blob','origin_test_git_blob'),('runtime/cli_v1/mcp_server.py','extracted_server_git_blob','origin_server_git_blob')]:
 b=subprocess.check_output(['git','hash-object',str(asset/'repo'/rel)],cwd=repo,text=True).strip(); ck('source_'+rel.replace('/','_'),b==cor[ef]==cor[of])
s=j(packet/'inputs/INPUTS-SUMMARY.json')
for n in ('repo','deps','stage','xkb','runner'):
 p=packet/'inputs'/f'{n.upper()}-MANIFEST.json'; m=j(p); ck(n+'_manifest_hash',sha(p)==s[n]['manifest_sha256']); ck(n+'_manifest_count',m['files']==len(m['entries'])==s[n]['files'] and m['bytes']==s[n]['bytes'])
ck('readiness_gate',ready['readiness_state']=='READY_FOR_SINGLE_FRESH_SESSION' and ready['archive_match'] and ready['harness_build_exit_zero'] and ready['input_manifests_finalized'])
br=j(packet/'HARNESS-BUILD-RESULT.json'); ck('offline_harness_build',br['restore_exit_code']==br['build_exit_code']==br['warnings']==br['errors']==0 and br['dll_sha256']==ready['harness_build_dll_sha256'].lower())
log=(out/'wslc-host-harness.log').read_text(encoding='utf-8-sig')
ck('wslc_303_and_exact_name','"Major":3' in log and '"Minor":0' in log and '"Revision":3' in log and '"filter":"name='+inv['container_name']+'","stdout":"","stderr":""' in log)
ck('no_global_inventory_or_docker','container list --all' not in log and 'docker.exe' not in log.lower() and 'docker ' not in log.lower())
ck('network_none_readonly_mounts',all(x in log for x in ['"network":"none"','"repo_read_only":true','"deps_read_only":true','"stage_read_only":true','"xkb_read_only":true','"runner_read_only":true']))
ck('exact_cleanup',cleanup['sessionName']==inv['session_name'] and cleanup['containerName']==inv['container_name'] and cleanup['deleted'] and cleanup['imageDeleted'] and cleanup['terminated'] and cleanup['failure'] is None and cleanup['exit']==0 and cleanup['cid']==(out/'container.cid').read_text().strip())
ck('test_exit_and_xvfb_cleanup',(out/'test-exit-code.txt').read_text().strip()=='0' and 'Ran 1 test' in (out/'runner.stderr.txt').read_text(encoding='utf-8-sig') and 'OK' in (out/'runner.stderr.txt').read_text(encoding='utf-8-sig') and (out/'preflight-status.txt').read_text().strip()=='pass' and (out/'xvfb-process-absent-after-run.txt').read_text().strip().lower()=='true')
ck('3935_pause',result['xvfb_server_pause']['requested_pause_ms']==3935 and result['xvfb_server_pause']['observed_pause_ms']>=3935 and result['xvfb_server_pause']['signal_identity']=='retained_pidfd' and result['xvfb_server_pause']['resume_receipt']['error'] is None)
tx=result['cancel']['cancellation']; start=tx['admitted_monotonic_ns']; done=tx['completed_monotonic_ns']; deadline=tx['transaction_deadline_monotonic_ns']; rel=tx['result']['owner_release_attempt']['release']; ind=result['independent_release_readback']; hor=result['late_request_horizon_readback']; relms=(rel['readback_monotonic_ns']-start)/1e6; indms=(ind['observed_ns']-start)/1e6; txms=(done-start)/1e6
ck('transaction_within_4s',deadline-start==4000000000 and done<=deadline and txms<=4000)
ck('caller_cancel_under_3s',result['cancel_elapsed_ms']<3000)
ck('release_readback_within_4s',tx['result']['owner_release_attempt']['status']=='readback_verified' and rel['verified'] and relms<=4000)
ck('independent_readback_within_5s',ind['keys_down']=={'a':False,'b':False} and indms<=5000)
ck('late_horizon_clean',hor['ms_after_cancel_start']>=8500 and hor['keys_down']=={'a':False,'b':False,'c':False} and not hor['late_keypress_b_observed'])
old=result['independent_task_oracle']; rec=result['fresh_session_recovery']
ck('initial_task_oracle',old['status']=='pass' and all(old['checks'].values()) and old['task_success'] is True)
ck('fresh_task_oracle',rec['task_oracle']['status']=='pass' and all(rec['task_oracle']['checks'].values()) and rec['task_oracle']['task_success'] is True and rec['effect_count_before_input']==[0] and rec['effect_count_after_input']==[1] and rec['effect_count_at_horizon']==[1])
ck('old_attempt_unknown_no_replay',tx['result']['cleanup_status']=='UNKNOWN' and tx['result']['release_confirmed'] is False and tx['result']['replay_allowed'] is False and tx['result']['task_success'] is None and result['terminal']['task_success'] is None and rec['old_cancellation_fence']=={'cleanup_status':'UNKNOWN','late_server_request_possible':True,'release_confirmed':False,'replay_allowed':False})
ck('fresh_close_verified',result['fresh_session_close']['status']=='closed' and result['fresh_session_close']['verified'] and result['fresh_session_close']['release_confirmed'])
st=asset/'session-storage-s29'/'storage.vhdx'; ck('session_storage_retained_hash',post['status']=='session_terminated_storage_retained' and post['session_termination_confirmed'] and not post['cleanup_attempted'] and st.is_file() and st.stat().st_size==post['bytes'] and sha(st)==post['sha256'])
r=j(packet/'REDACTIONS.json'); ck('redaction_hashes',all(sha(packet/x['path'])==x['sanitized_sha256'] for x in r['redactions']))
ck('raw_result_preserved',sha(xout/'result.json')==sha(out/'result.json') and sha(xout/'xvfb.log')==sha(out/'xvfb.log'))
classification='PASS_SCOPED_3935MS_REPLICATE' if all(checks.values()) else 'FAIL_OR_INCOMPLETE_AUDIT'
report={'schema':'agent-interface/wslc-s29-independent-audit-v1','attempt_id':pre['attempt_id'],'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'evidence_checks':checks,'evidence_counts':{'passed':sum(checks.values()),'total':len(checks)},'failed_evidence_checks':[k for k,v in checks.items() if not v],'observations':{'requested_pause_ms':3935,'observed_pause_ms':result['xvfb_server_pause']['observed_pause_ms'],'public_cancel_response_ms':result['cancel_elapsed_ms'],'release_readback_ms_from_admission':relms,'independent_readback_ms_from_admission':indms,'transaction_ms':txms,'transaction_margin_ms':(deadline-done)/1e6,'late_horizon_ms':hor['ms_after_cancel_start'],'initial_task_oracle':old['status'],'fresh_task_oracle':rec['task_oracle']['status'],'fresh_input_to_effect_readback_ms':rec['effect_timing_ms']['input_invocation_to_effect_readback_completed'],'runtime_cleanup_status':tx['result']['cleanup_status'],'runtime_release_confirmed':tx['result']['release_confirmed'],'runtime_replay_allowed':tx['result']['replay_allowed'],'runtime_task_success':tx['result']['task_success'],'container_removed':cleanup['deleted'],'image_removed':cleanup['imageDeleted'],'session_terminated':cleanup['terminated'],'session_storage_bytes':post['bytes'],'session_storage_sha256':post['sha256']}}
(packet/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
(packet/'AUDIT-EXECUTION.log').write_text(json.dumps({'classification':classification,'passed':sum(checks.values()),'total':len(checks),'failed':report['failed_evidence_checks'],'observations':report['observations']},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'classification':classification,'passed':sum(checks.values()),'total':len(checks),'failed':report['failed_evidence_checks'],'observations':report['observations']},indent=2)); sys.exit(0 if all(checks.values()) else 1)
