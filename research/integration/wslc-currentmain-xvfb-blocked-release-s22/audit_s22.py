import datetime,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent; repo=root.parents[2]; out=root/'output'; inv=json.loads((root/'INVOCATION-METADATA.json').read_text(encoding='utf-8-sig')); pre=json.loads((root/'PREREGISTRATION.json').read_text(encoding='utf-8-sig')); cond=json.loads((root/'CONDITIONS.json').read_text(encoding='utf-8-sig')); r=json.loads((out/'result.json').read_text()); checks={}
def ck(k,v): checks[k]=bool(v)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
ck('attempt_and_commit_pins',pre['attempt_id']==cond['attempt_id']==inv['attempt_id']=='wslc-standard-caller-xvfb-20261025-s22' and pre['source_commit']==cond['source_commit']==inv['source_commit'])
ck('runner_init_pinned',sha(root/'runner/run-container.py')==pre['runner_sha256']==inv['runner_sha256'] and sha(root/'runner/container-init.sh')==pre['init_sha256']==inv['init_sha256'] and b'\r' not in (root/'runner/container-init.sh').read_bytes())
ck('harness_pinned',sha(root/'harness/Program.cs')==inv['harness_source_sha256'])
for rel,digest in pre['source_hashes'].items():
 ck('source_sha_'+rel.replace('/','_'),sha(repo/rel)==digest)
 tree=subprocess.run(['git','rev-parse',f"{pre['source_commit']}:{rel}"],cwd=repo,capture_output=True,text=True)
 work=subprocess.run(['git','hash-object','--path='+rel,rel],cwd=repo,capture_output=True,text=True)
 ck('commit_blob_'+rel.replace('/','_'),tree.returncode==work.returncode==0 and tree.stdout.strip()==work.stdout.strip())
for key in ('deps','stage','xkb'):
 m=json.loads((root/f'inputs/{key}-manifest.json').read_text(encoding='utf-8-sig')); base=Path(m['source']); good=True; total=0
 files=sorted(x for x in base.rglob('*') if x.is_file())
 if len(files)!=m['file_count']: good=False
 for item in m['files']:
  p=base.joinpath(*item['path'].split('/')); total+=item['bytes']
  if not p.is_file() or p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:good=False
 if total!=m['total_bytes']:good=False
 ck(key+'_manifest_hashes',good)
setup=json.loads((out/'container-setup.json').read_text()); cleanup=json.loads((out/'resource-cleanup.json').read_text())
ck('xres_identity_preflight',(out/'preflight-status.txt').read_text().strip()=='pass' and 'local_xres_identity=' in (out/'xvfb-process-identity-preflight.txt').read_text())
ck('wslc_runtime_cleanup',setup.get('returncode')==0 and cleanup.get('failure') is None and cleanup['started'] and cleanup['terminated'] and cleanup['pulled'] and cleanup['imageDeleted'] and cleanup['deleted'] and cleanup['exit']==0 and cleanup['sessionName']==inv['session_name'] and cleanup['containerName']==inv['container_name'] and cleanup['image']==inv['image'])
log=(out/'wslc-host-harness.log').read_text(); ck('network_none_and_readonly_mounts',all(x in log for x in ['"network":"none"','"repo_read_only":true','"deps_read_only":true','"stage_read_only":true','"xkb_read_only":true','"runner_read_only":true']))
ck('caller_test_passed',(out/'test-exit-code.txt').read_text().strip()=='0' and 'Ran 1 test' in (out/'runner.stderr.txt').read_text() and 'OK' in (out/'runner.stderr.txt').read_text())
pause=r['xvfb_server_pause']; ck('3860ms_pidfd_pause',pause['requested_pause_ms']==3860 and pause['observed_pause_ms']>=3860 and pause['signal_identity']=='retained_pidfd' and pause['resume_receipt']['error'] is None)
tx=r['cancel']['cancellation']; start=tx['admitted_monotonic_ns']; deadline=tx['transaction_deadline_monotonic_ns']; release=r['independent_release_readback']; readback_ms=(release['observed_ns']-r['timing_ns']['cancel_started'])/1e6; margin_ms=(deadline-release['owner_release_attempt']['release']['readback_monotonic_ns'])/1e6; elapsed_ms=(release['owner_release_attempt']['release']['readback_monotonic_ns']-start)/1e6
ck('exact_4s_transaction',deadline-start==4_000_000_000)
ck('release_before_deadline',release['owner_release_attempt']['status']=='readback_verified' and release['owner_release_attempt']['release']['verified'] is True and release['owner_release_attempt']['release']['readback_monotonic_ns']<=deadline)
ck('independent_readback_within_5s',readback_ms<=5000 and release['keys_down']=={'a':False,'b':False})
late=r['late_request_horizon_readback']; ck('all_up_at_delayed_horizon',late['keys_down']=={'a':False,'b':False,'c':False} and late['late_keypress_b_observed'] is False and late['ms_after_cancel_start']>=8500)
tasks=r['counted_task_outcomes']; old=r['independent_task_oracle']; fresh=r['fresh_session_recovery']['task_oracle']; ck('old_and_fresh_effect_oracles',tasks['old_task']=='pass' and tasks['fresh_task']=='pass' and old['status']=='pass' and old['task_success'] is True and fresh['status']=='pass' and fresh['task_success'] is True and all(old['checks'].values()) and all(fresh['checks'].values()))
ck('unknown_and_replay_fence',r['cancel']['cleanup_status']=='UNKNOWN' and r['cancel']['release_confirmed'] is False and r['cancel']['replay_allowed'] is False and r['cancel']['task_success'] is None and r['cancel']['late_server_request_possible'] is True)
ck('public_cancel_response_bound',r['cancel_elapsed_ms']<3000)
ck('xvfb_process_terminated',(out/'xvfb-process-absent-after-run.txt').read_text().strip().lower()=='true')
classification='PASS_SCOPED_4S_TRANSACTION_3860MS_W SLC_REPLICATE'.replace(' ','') if all(checks.values()) else 'FAIL_OR_INCOMPLETE_AUDIT'
raw=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name not in {'AUDIT.json','AUDIT-EXECUTION.log','OUTCOME.json','RESULT.md'}: raw.append({'path':p.relative_to(repo).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
report={'schema':'wslc-s22-boundary-audit-v1','attempt_id':pre['attempt_id'],'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'evidence_checks':checks,'evidence_counts':{'passed':sum(checks.values()),'total':len(checks)},'failed_evidence_checks':[k for k,v in checks.items() if not v],'observations':{'runtime':'WSLc 3.0.3','requested_pause_ms':3860,'observed_pause_ms':pause['observed_pause_ms'],'test_exit_code':0 if checks['caller_test_passed'] else None,'public_cancel_response_ms':r['cancel_elapsed_ms'],'release_readback_from_admission_ms':elapsed_ms,'release_deadline_margin_ms':margin_ms,'independent_readback_after_cancel_start_ms':readback_ms,'late_horizon_after_cancel_start_ms':late['ms_after_cancel_start'],'runtime_cleanup_status':r['cancel']['cleanup_status'],'runtime_release_confirmed':r['cancel']['release_confirmed'],'runtime_replay_allowed':r['cancel']['replay_allowed'],'runtime_task_success':r['cancel']['task_success'],'old_task_oracle':old['status'],'fresh_task_oracle':fresh['status'],'container_removed':cleanup['deleted'],'image_removed':cleanup['imageDeleted'],'session_terminated':cleanup['terminated'],'resource_delta_from_r46':'WSLc settings requested CPU 2/memory 2048 MB/GPU disabled/network none; WSLc container API did not record Docker-only pids_limit or tmpfs settings.'},'raw_files':raw}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'classification':classification,'passed':sum(checks.values()),'total':len(checks),'failed':report['failed_evidence_checks'],'release_ms_from_admission':elapsed_ms,'deadline_margin_ms':margin_ms,'independent_readback_ms':readback_ms,'horizon_ms':late['ms_after_cancel_start']},indent=2))

