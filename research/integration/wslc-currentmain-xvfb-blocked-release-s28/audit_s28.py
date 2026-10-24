import datetime,hashlib,json,os,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parent; repo=root.parents[2]; out=root/'output'; failures=[]; checks={}
def ck(name, condition): checks[name]=bool(condition)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
pre=json.loads((root/'PREREGISTRATION.json').read_text()); cond=json.loads((root/'CONDITIONS.json').read_text()); inv=json.loads((root/'INVOCATION-METADATA.json').read_text()); result=json.loads((out/'result.json').read_text()); log=(out/'wslc-host-harness.log').read_text(encoding='utf-8'); setup=json.loads((out/'container-setup.json').read_text()); cleanup=json.loads((out/'resource-cleanup.json').read_text())
ck('attempt_binding', pre['attempt_id']==cond['attempt_id']==inv['attempt_id']=='wslc-standard-caller-xvfb-20261025-s28')
ck('current_main_source',pre['source_commit']==cond['source_commit']==inv['source_commit']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip())
for rel,want in pre['source_hashes'].items(): ck('source_'+rel.replace('/','_'),(repo/rel).is_file() and sha(repo/rel)==want and subprocess.check_output(['git','rev-parse',f"{pre['source_commit']}:{rel}"],cwd=repo,text=True).strip()==subprocess.check_output(['git','hash-object','--path='+rel,rel],cwd=repo,text=True).strip())
ck('runner_pins',sha(root/'runner/run-container.py')==pre['runner_sha256']==inv['runner_sha256'] and sha(root/'runner/container-init.sh')==pre['init_sha256']==inv['init_sha256'] and b'\r' not in (root/'runner/container-init.sh').read_bytes() and sha(root/'harness/Program.cs')==pre['harness_source_sha256']==inv['harness_source_sha256'])
ck('build_pass', (root/'HARNESS-BUILD-EXIT-CODE.txt').read_text().strip()=='0' and 'ビルドに成功しました' in (root/'HARNESS-BUILD.log').read_text(encoding='utf-8'))
for key in ('deps','stage','xkb'):
 m=json.loads((root/f'inputs/{key}-manifest.json').read_text()); env=os.environ.get('S27_'+key.upper()+'_ROOT'); base=pathlib.Path(env) if env else pathlib.Path(m['source']); files=[p for p in base.rglob('*') if p.is_file()]; good=len(files)==m['file_count']
 for item in m['files']:
  f=base.joinpath(*item['path'].split('/'))
  if not f.is_file() or f.stat().st_size!=item['bytes'] or sha(f)!=item['sha256']: good=False; break
 ck(key+'_asset_manifest',good)
ck('pinned_wslc_and_exact_name_preflight','"Major":3' in log and '"Minor":0' in log and '"Revision":3' in log and '"exit":0,"filter":"name='+inv['container_name']+'","stdout":"","stderr":""' in log)
ck('no_global_inventory_or_docker', '"filter":"name='+inv['container_name']+'"' in log and 'container list --all' not in log and 'docker.exe' not in log.lower() and 'docker ' not in log.lower())
ck('network_none_readonly',all(v in log for v in ['"network":"none"','"repo_read_only":true','"deps_read_only":true','"stage_read_only":true','"xkb_read_only":true','"runner_read_only":true']))
ck('full_cid_and_exact_cleanup',len((out/'container.cid').read_text().strip())==64 and cleanup['cid']==(out/'container.cid').read_text().strip() and cleanup['deleted'] and cleanup['imageDeleted'] and cleanup['terminated'] and cleanup['failure'] is None and cleanup['sessionName']==inv['session_name'] and cleanup['containerName']==inv['container_name'])
ck('test_started_after_local_xres_preflight',(out/'preflight-status.txt').read_text().strip()=='pass' and 'local_xres_identity=' in (out/'xvfb-process-identity-preflight.txt').read_text() and (out/'trial-started.txt').exists())
ck('test_exit_pass',(out/'test-exit-code.txt').read_text().strip()=='0' and 'OK' in (out/'runner.stderr.txt').read_text())
ck('trial_conditions',result['xvfb_server_pause']['requested_pause_ms']==3930 and result['xvfb_server_pause']['observed_pause_ms']>=3930 and result['xvfb_server_pause']['signal_identity']=='retained_pidfd' and result['xvfb_server_pause']['resume_receipt']['error'] is None)
tx=result['cancel']['cancellation']; start=tx['admitted_monotonic_ns']; done=tx['completed_monotonic_ns']; deadline=tx['transaction_deadline_monotonic_ns']; release=tx['result']['owner_release_attempt']['release']; ck('transaction_within_4s',deadline-start==4_000_000_000 and done<=deadline)
ck('caller_cancel_under_3s',result['cancel_elapsed_ms']<3000)
ck('release_readback_within_deadline',tx['result']['owner_release_attempt']['status']=='readback_verified' and release['verified'] and (release['readback_monotonic_ns']-start)<=4_000_000_000)
ind=result['independent_release_readback']; ck('independent_readback_within_5s',ind['keys_down']=={'a':False,'b':False} and (ind['observed_ns']-start)<=5_000_000_000)
horizon=result['late_request_horizon_readback']; ck('late_horizon_clean',horizon['ms_after_cancel_start']>=8500 and horizon['keys_down']=={'a':False,'b':False,'c':False} and not horizon['late_keypress_b_observed'])
old=result['independent_task_oracle']; ck('old_task_effect_oracle',old['status']=='pass' and all(old['checks'].values()) and result['effect_before_cancel']['property_value']==[1])
rec=result['fresh_session_recovery']; ck('bounded_fresh_session_recovery',rec['task_oracle']['status']=='pass' and all(rec['task_oracle']['checks'].values()) and rec['task_oracle']['task_success'] is True and rec['old_cancellation_fence']=={'cleanup_status':'UNKNOWN','late_server_request_possible':True,'release_confirmed':False,'replay_allowed':False})
ck('runtime_unknown_no_replay',tx['result']['cleanup_status']=='UNKNOWN' and tx['result']['release_confirmed'] is False and tx['result']['replay_allowed'] is False and tx['result']['task_success'] is None and result['terminal']['task_success'] is None)
ck('fresh_close_verified',result['fresh_session_close']['status']=='closed' and result['fresh_session_close']['verified'] and result['fresh_session_close']['release_confirmed'])
ck('xvfb_process_terminated',(out/'xvfb-process-absent-after-run.txt').read_text().strip().lower()=='true')
storage=json.loads((root/'POST_CLEANUP.json').read_text()); ck('terminated_session_storage_retained_with_hash',storage['status']=='session_terminated_storage_retained' and storage['session_termination_confirmed'] and not storage['cleanup_attempted'] and storage['file']=='storage.vhdx' and storage['bytes']>0 and len(storage['sha256'])==64)
redactions=root/'REDACTIONS.json'
if redactions.exists():
 recd=json.loads(redactions.read_text()); ck('privacy_redaction_hashes',all(sha(root/x['path'])==x['sanitized_sha256'] for x in recd['redactions']))
else: checks['privacy_redaction_hashes']=True
classification='PASS_SCOPED_3930MS_REPLICATE' if all(checks.values()) else 'FAIL_OR_INCOMPLETE_AUDIT'
raw=[]
for f in sorted(root.rglob('*')):
 if f.is_file() and f.name not in {'AUDIT.json','AUDIT-EXECUTION.log','OUTCOME.json','RESULT.md','PACKET_SHA256SUMS','RAW_SHA256SUMS','AUDIT-SHA256.txt'} and 'bin' not in f.parts and 'obj' not in f.parts: raw.append({'path':f.relative_to(repo).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size})
release_ms=(release['readback_monotonic_ns']-start)/1e6; independent_ms=(ind['observed_ns']-start)/1e6; tx_ms=(done-start)/1e6
report={'schema':'wslc-s28-boundary-audit-v1','attempt_id':pre['attempt_id'],'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'evidence_checks':checks,'evidence_counts':{'passed':sum(checks.values()),'total':len(checks)},'failed_evidence_checks':[k for k,v in checks.items() if not v],'observations':{'requested_pause_ms':3930,'observed_pause_ms':result['xvfb_server_pause']['observed_pause_ms'],'public_cancel_response_ms':result['cancel_elapsed_ms'],'release_readback_ms_from_admission':release_ms,'independent_readback_ms_from_admission':independent_ms,'transaction_ms':tx_ms,'transaction_margin_ms':(deadline-done)/1e6,'late_horizon_ms':horizon['ms_after_cancel_start'],'old_task_oracle':old['status'],'fresh_task_oracle':rec['task_oracle']['status'],'runtime_cleanup_status':tx['result']['cleanup_status'],'runtime_release_confirmed':tx['result']['release_confirmed'],'runtime_replay_allowed':tx['result']['replay_allowed'],'runtime_task_success':tx['result']['task_success'],'container_removed':cleanup['deleted'],'image_removed':cleanup['imageDeleted'],'session_terminated':cleanup['terminated']},'raw_files':raw}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
(root/'AUDIT-EXECUTION.log').write_text(json.dumps({'classification':classification,'passed':sum(checks.values()),'total':len(checks),'failed':report['failed_evidence_checks'],'transaction_ms':tx_ms,'release_readback_ms':release_ms,'independent_readback_ms':independent_ms,'late_horizon_ms':horizon['ms_after_cancel_start']},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'classification':classification,'passed':sum(checks.values()),'total':len(checks),'failed':report['failed_evidence_checks'],'observations':report['observations']},indent=2))
sys.exit(not all(checks.values()))


