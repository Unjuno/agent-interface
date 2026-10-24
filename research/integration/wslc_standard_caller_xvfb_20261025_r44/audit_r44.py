import datetime, hashlib, json, subprocess
from pathlib import Path

root=Path(__file__).resolve().parent; repo=root.parents[2]; out=root/'output'
load=lambda p: json.loads((root/p).read_text(encoding='utf-8-sig'))
pre,cond,inv=(load('PREREGISTRATION.json'),load('CONDITIONS.json'),load('INVOCATION-METADATA.json'))
r=load('output/result.json'); checks={}
def check(k,v): checks[k]=bool(v)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
check('attempt_pins',pre['attempt_id']==cond['attempt_id']==inv['attempt_id']=='wslc-standard-caller-xvfb-20261025-r44' and pre['source_commit']==cond['source_commit'])
for rel,digest in pre['source_hashes'].items():
 check('raw_sha_'+rel.replace('/','_'),sha(repo/rel)==digest)
 tree=subprocess.run(['git','rev-parse',f"{pre['source_commit']}:{rel}"],cwd=repo,capture_output=True,text=True)
 work=subprocess.run(['git','hash-object','--path='+rel,rel],cwd=repo,capture_output=True,text=True)
 check('commit_blob_'+rel.replace('/','_'),tree.returncode==work.returncode==0 and tree.stdout.strip()==work.stdout.strip())
state=(out/'container-state-before-cleanup.txt').read_text(); mounts=(out/'container-mounts-before-cleanup.txt').read_text().splitlines(); stderr=(out/'runner.stderr.txt').read_text()
check('image_digest',pre['image'] in (out/'pinned-image-inspect.txt').read_text() and pre['image'] in state)
check('network_and_limits',' none ' in state and '2147483648' in state and '2000000000' in state and '128' in state)
check('readonly_mounts',all(f'{p}:readonly=true' in mounts for p in ['/repo','/deps','/stage','/xkb']) and '/out:readonly=false' in mounts)
check('exec_tmpfs','rw,exec,nosuid,nodev,mode=1777,size=512m' in state)
check('xres_preflight',(out/'preflight-status.txt').read_text().strip()=='pass' and 'local_xres_identity=' in (out/'xvfb-process-identity-preflight.txt').read_text())
pause=r['xvfb_server_pause']; check('3875ms_pidfd_pause',pause['requested_pause_ms']==3875 and pause['observed_pause_ms']>=3875 and pause['signal_identity']=='retained_pidfd' and pause['resume_receipt']['error'] is None)
test_exit=(out/'test-exit-code.txt').read_text().strip(); docker_exit=(out/'docker-run-exit-code.txt').read_text().strip()
check('runner_and_test_exit_agree',docker_exit==test_exit)
tx=r['cancel']['cancellation']; start,deadline,completed=tx['admitted_monotonic_ns'],tx['transaction_deadline_monotonic_ns'],tx['completed_monotonic_ns']; overrun=(completed-deadline)/1e6
check('exact_4s_transaction',deadline-start==4_000_000_000)
release=r.get('independent_release_readback'); tasks=r.get('counted_task_outcomes'); old=r.get('independent_task_oracle'); fresh=r.get('fresh_session_recovery')
pass_path=test_exit=='0' and release is not None and tasks is not None and old is not None and fresh is not None
fail_path=test_exit=='1' and completed>deadline and r['cancel']['cleanup_status']=='UNKNOWN' and r['cancel']['replay_allowed'] is False and release is None and tasks is None
check('outcome_matches_one_registered_branch',pass_path or fail_path)
if pass_path:
 check('release_before_deadline',release['owner_release_attempt']['status']=='readback_verified' and release['owner_release_attempt']['release']['verified'] is True and release['owner_release_attempt']['release']['readback_monotonic_ns']<=deadline)
 check('all_up_readback_and_horizon',release['keys_down']=={'a':False,'b':False} and r['late_request_horizon_readback']['keys_down']=={'a':False,'b':False,'c':False} and r['late_request_horizon_readback']['late_keypress_b_observed'] is False and r['late_request_horizon_readback']['ms_after_cancel_start']>=8500)
 readback_ms=(release['observed_ns']-r['timing_ns']['cancel_started'])/1e6
 margin_ms=(deadline-release['owner_release_attempt']['release']['readback_monotonic_ns'])/1e6
 check('independent_readback_within_5s',readback_ms<=5000)
 check('both_task_oracles',tasks['old_task']=='pass' and tasks['fresh_task']=='pass' and old['status']=='pass' and fresh['task_oracle']['status']=='pass')
 check('unknown_fence_preserved',r['cancel']['cleanup_status']=='UNKNOWN' and r['cancel']['release_confirmed'] is False and r['cancel']['replay_allowed'] is False and r['cancel']['task_success'] is None)
 classification='PASS_SCOPED_4S_TRANSACTION_3875MS'
else:
 check('transaction_boundary_failure_recorded',fail_path and ('transaction_deadline' in stderr or 'unretired_or_late_supervisor' in stderr) and 'FAILED (failures=1)' in stderr)
 check('release_unknown_and_replay_denied',r['cancel']['owner_release_attempt']['status']=='unknown' and r['cancel']['owner_release_attempt']['reason'] in {'transaction_deadline','unretired_or_late_supervisor'} and r['cancel']['task_success'] is None)
 check('no_release_or_task_claim',release is None and tasks is None and old is None and fresh is None)
 classification='FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN'
check('public_cancel_response_bound',r['cancel_elapsed_ms']<3000)
check('xvfb_stopped',(out/'xvfb-process-absent-after-run.txt').read_text().strip().lower()=='true')
check('exact_container_removed',(out/'docker-cleanup-exit-code.txt').read_text().strip()=='0' and (out/'container-inspect-after-cleanup-exit-code.txt').read_text().strip()!='0' and 'no such container' in (out/'container-inspect-after-cleanup.txt').read_text().lower())
stage=json.loads((repo/'research/integration/wslc_standard_caller_xvfb_20261025_r33/STAGE-MANIFEST.json').read_text(encoding='utf-8-sig')); sr=repo/'research/integration/wslc_standard_caller_xvfb_20261025_r16/stage'
check('stage_hashes',len(stage)==1252 and all(sha(sr/x['path'])==x['sha256'] for x in stage))
xkb=json.loads((repo/'research/integration/wslc_standard_caller_xvfb_20261025_r34/xkb-materialization.json').read_text(encoding='utf-8-sig')); xr=repo/'research/integration/wslc_standard_caller_xvfb_20261025_r34/xkb-materialized'
check('xkb_hashes',xkb['files']==293 and all(sha(xr/x['path'])==x['sha256'] for x in xkb['manifest']))
raw=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name not in {'AUDIT.json','AUDIT-EXECUTION.log','OUTCOME.json','RESULT.md'}: raw.append({'path':p.relative_to(repo).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
report={'schema':'wslc-r44-boundary-audit-v1','attempt_id':pre['attempt_id'],'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'evidence_checks':checks,'evidence_counts':{'passed':sum(checks.values()),'total':len(checks)},'failed_evidence_checks':[k for k,v in checks.items() if not v],'observations':{'requested_pause_ms':3875,'observed_pause_ms':pause['observed_pause_ms'],'test_exit_code':int(test_exit),'cancel_response_ms':r['cancel_elapsed_ms'],'transaction_elapsed_ms':(completed-start)/1e6,'release_deadline_margin_ms':margin_ms if release is not None else None,'independent_readback_ms_after_cancel_start':readback_ms if release is not None else None,'late_horizon_ms':r['late_request_horizon_readback']['ms_after_cancel_start'] if release is not None else None,'supervisor_release_status':release['owner_release_attempt']['status'] if release is not None else 'UNKNOWN','runtime_cleanup_status':r['cancel']['cleanup_status'],'runtime_release_confirmed':r['cancel']['release_confirmed'],'runtime_replay_allowed':r['cancel']['replay_allowed'],'runtime_task_success':r['cancel']['task_success'],'task_oracles_reached':tasks is not None,'container_removed':checks['exact_container_removed']},'raw_files':raw}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
lines=[f'classification={classification}',f'evidence_checks={sum(checks.values())}/{len(checks)}']+[f'{k}={"PASS" if v else "FAIL"}' for k,v in checks.items()]
(root/'AUDIT-EXECUTION.log').write_text('\n'.join(lines)+'\n',encoding='utf-8')
outcome={'attempt_id':pre['attempt_id'],'classification':classification,'evidence_checks_passed':sum(checks.values()),'evidence_checks_total':len(checks),'caller_test_exit_code':int(test_exit),'release_status':r['cancel']['cleanup_status'],'independent_release_readback':release is not None,'task_oracles_reached':tasks is not None,'retries':0,'container_removed':checks['exact_container_removed']}
(root/'OUTCOME.json').write_text(json.dumps(outcome,indent=2)+'\n',encoding='utf-8')
if pass_path:
 summary=f'''# R44 — WSLc 3.875 s pause under a 4 s transaction deadline

**Disposition: `{classification}` ({sum(checks.values())}/{len(checks)} evidence checks).** The unchanged public standard-caller test passed in a digest-pinned, network-disabled Ubuntu container. Xvfb paused for {pause['observed_pause_ms']:.3f} ms and resumed through its retained pidfd. Supervisor release/readback completed {margin_ms:.3f} ms before the transaction deadline; a separate parent readback arrived at +{readback_ms:.3f} ms, and the late-event horizon and both synthetic task oracles passed. Runtime cancellation custody remained UNKNOWN, replay denied, and task success null. The Xvfb process and exact container were removed.

This is one synthetic-Xvfb boundary sample between R43's 3,850 ms pass and R42's 3,900 ms deadline failure. It is not a reliability estimate or evidence of Windows desktop, MAP01, real-app transfer, or matched efficiency.
'''
else:
 reason=r['cancel']['owner_release_attempt'].get('reason','unknown')
 summary=f'''# R44 — WSLc 3.875 s pause under a 4 s transaction deadline

**Disposition: `{classification}` ({sum(checks.values())}/{len(checks)} evidence checks).** The unchanged public standard-caller test failed once in the digest-pinned, network-disabled Ubuntu container. Xvfb paused for {pause['observed_pause_ms']:.3f} ms and resumed through its retained pidfd. The public cancel response took {r['cancel_elapsed_ms']:.3f} ms; the transaction elapsed {(completed-start)/1e6:.3f} ms against its exact 4,000 ms deadline, overrun {max(0,overrun):.3f} ms. The supervisor release status was UNKNOWN (`{reason}`), `release_confirmed=false`, replay denied, and `task_success=null`.

The test stopped at the caller assertion. No independent release readback, late-event horizon, or task oracle was completed. The Xvfb process and exact container were removed. This is a single synthetic-Xvfb boundary probe, not a reliability estimate or evidence of Windows desktop, MAP01, real-app transfer, or matched efficiency. No retry was made.
'''
(root/'RESULT.md').write_text(summary,encoding='utf-8')
print(classification,f"evidence_checks={sum(checks.values())}/{len(checks)}",f"overrun_ms={max(0,overrun):.3f}")
if not all(checks.values()): raise SystemExit('R44 evidence audit failed')
