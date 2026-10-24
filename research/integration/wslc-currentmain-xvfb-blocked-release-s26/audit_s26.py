import datetime,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent; repo=root.parents[2]; out=root/'output'; inv=json.loads((root/'INVOCATION-METADATA.json').read_text(encoding='utf-8-sig')); pre=json.loads((root/'PREREGISTRATION.json').read_text(encoding='utf-8-sig')); cond=json.loads((root/'CONDITIONS.json').read_text(encoding='utf-8-sig')); r=json.loads((out/'result.json').read_text()); checks={}
def ck(k,v): checks[k]=bool(v)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
ck('attempt_commit_pins',pre['attempt_id']==cond['attempt_id']==inv['attempt_id']=='wslc-standard-caller-xvfb-20261025-s26' and pre['source_commit']==cond['source_commit']==inv['source_commit'])
ck('execution_source_pins',sha(root/'runner/run-container.py')==pre['runner_sha256']==inv['runner_sha256'] and sha(root/'runner/container-init.sh')==pre['init_sha256']==inv['init_sha256'] and b'\r' not in (root/'runner/container-init.sh').read_bytes() and sha(root/'harness/Program.cs')==inv['harness_source_sha256'])
for rel,digest in pre['source_hashes'].items():
 ck('source_sha_'+rel.replace('/','_'),sha(repo/rel)==digest)
 tree=subprocess.run(['git','rev-parse',f"{pre['source_commit']}:{rel}"],cwd=repo,capture_output=True,text=True); work=subprocess.run(['git','hash-object','--path='+rel,rel],cwd=repo,capture_output=True,text=True); ck('commit_blob_'+rel.replace('/','_'),tree.returncode==work.returncode==0 and tree.stdout.strip()==work.stdout.strip())
for key in ('deps','stage','xkb'):
 m=json.loads((root/f'inputs/{key}-manifest.json').read_text(encoding='utf-8-sig')); base=Path(m['source']); files=sorted(x for x in base.rglob('*') if x.is_file()); good=len(files)==m['file_count']
 for x in m['files']:
  f=base.joinpath(*x['path'].split('/'))
  if not f.is_file() or f.stat().st_size!=x['bytes'] or sha(f)!=x['sha256']:good=False
 ck(key+'_manifest_hashes',good)
setup=json.loads((out/'container-setup.json').read_text()); cleanup=json.loads((out/'resource-cleanup.json').read_text()); log=(out/'wslc-host-harness.log').read_text()
ck('wslc_expected_test_failure_and_cleanup',setup.get('stage')=='test_finished' and setup.get('returncode')==1 and cleanup.get('failure',{}).get('message')=='runner returned nonzero' and cleanup['started'] and cleanup['terminated'] and cleanup['pulled'] and cleanup['imageDeleted'] and cleanup['deleted'] and cleanup['exit']==1 and cleanup['sessionName']==inv['session_name'] and cleanup['containerName']==inv['container_name'] and cleanup['image']==inv['image'])
ck('isolated_network_and_readonly_mounts',all(x in log for x in ['"network":"none"','"repo_read_only":true','"deps_read_only":true','"stage_read_only":true','"xkb_read_only":true','"runner_read_only":true']))
ck('private_xres_preflight_before_test',(out/'preflight-status.txt').read_text().strip()=='pass' and 'local_xres_identity=' in (out/'xvfb-process-identity-preflight.txt').read_text() and (out/'trial-started.txt').exists())
pause=r['xvfb_server_pause']; ck('3940ms_pidfd_pause',pause['requested_pause_ms']==3940 and pause['observed_pause_ms']>=3940 and pause['signal_identity']=='retained_pidfd' and pause['resume_receipt']['error'] is None)
tx=r['cancel']['cancellation']; start=tx['admitted_monotonic_ns']; deadline=tx['transaction_deadline_monotonic_ns']; completed=tx['completed_monotonic_ns']; ck('exact_4s_transaction_overrun',deadline-start==4_000_000_000 and completed>deadline)
ck('deadline_overrun_is_explicit',r['status']=='FAIL' and tx['completed_monotonic_ns']>deadline and r['cancel']['owner_release_attempt']['status']=='unknown' and r['cancel']['owner_release_attempt']['reason']=='transaction_deadline' and 'transaction_deadline' in (out/'runner.stderr.txt').read_text())
ck('unknown_no_replay_no_task_fence',r['cancel']['cleanup_status']=='UNKNOWN' and r['cancel']['release_confirmed'] is False and r['cancel']['replay_allowed'] is False and r['cancel']['task_success'] is None and r['cancel']['late_server_request_possible'] is True)
ck('no_release_or_task_success_claim',r.get('independent_release_readback') is None and r.get('counted_task_outcomes') is None and r.get('independent_task_oracle') is None and r.get('fresh_session_recovery') is None)
ck('no_test_exit_pass', (out/'test-exit-code.txt').read_text().strip()=='1' and 'FAILED (failures=1)' in (out/'runner.stderr.txt').read_text())
ck('public_cancel_response_bound',r.get('cancel_elapsed_ms',999999)<3000)
ck('xvfb_stopped',(out/'xvfb-process-absent-after-run.txt').read_text().strip().lower()=='true')
classification='FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN' if all(checks.values()) else 'FAIL_OR_INCOMPLETE_AUDIT'
raw=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name not in {'AUDIT.json','AUDIT-EXECUTION.log','OUTCOME.json','RESULT.md'}:raw.append({'path':p.relative_to(repo).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
over_ms=(completed-deadline)/1e6
report={'schema':'wslc-s26-deadline-boundary-audit-v1','attempt_id':pre['attempt_id'],'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'evidence_checks':checks,'evidence_counts':{'passed':sum(checks.values()),'total':len(checks)},'failed_evidence_checks':[k for k,v in checks.items() if not v],'observations':{'requested_pause_ms':3940,'observed_pause_ms':pause['observed_pause_ms'],'test_exit_code':1,'deadline_overrun_ms':over_ms,'transaction_elapsed_ms':(completed-start)/1e6,'public_cancel_response_ms':r['cancel_elapsed_ms'],'runtime_cleanup_status':r['cancel']['cleanup_status'],'runtime_release_confirmed':r['cancel']['release_confirmed'],'runtime_replay_allowed':r['cancel']['replay_allowed'],'runtime_task_success':r['cancel']['task_success'],'release_receipt':'UNKNOWN','task_effect_oracles':'not emitted on boundary failure','container_removed':cleanup['deleted'],'image_removed':cleanup['imageDeleted'],'session_terminated':cleanup['terminated']},'raw_files':raw}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'classification':classification,'passed':sum(checks.values()),'total':len(checks),'failed':report['failed_evidence_checks'],'overrun_ms':over_ms,'transaction_ms':(completed-start)/1e6},indent=2))

