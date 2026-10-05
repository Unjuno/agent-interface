from pathlib import Path
import hashlib,json,os,subprocess,sys
root=Path(r'C:\s15e'); runs=root/'runs'
if not (root/'PREPARED.json').is_file(): raise SystemExit('REFUSE: A06 staging did not complete')
if runs.exists(): raise SystemExit('REFUSE: A06 run output already exists')
runs.mkdir()
modules=['test_input_owner_v12_cleanup_measurement.CleanupMeasurementTests','test_input_owner_v12_key_measurement','test_input_owner_v12_batch_sample_custody','test_batch_key_measurement_composition','test_input_owner_v12_explicit_up_cancel','test_input_owner_v12_wheel_cleanup','test_input_transition_owner_v4']
python=r'C:\Users\junny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
env=os.environ.copy(); env['PYTHONPATH']=';'.join([str(root),str(root/'research/live_control'),str(root/'research/doom'),str(root/'research/observation_tiles'),str(root/'research/observation_gating'),str(root/'research/real_apps_v1')])
records={}
for mode,args in [('normal',['-B']),('optimized',['-O','-B'])]:
 argv=[python,*args,'-m','unittest','-v',*modules]
 result=subprocess.run(argv,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 stdout_path=runs/f'{mode}.stdout.txt'; stderr_path=runs/f'{mode}.stderr.txt'; stdout_path.write_bytes(result.stdout); stderr_path.write_bytes(result.stderr)
 records[mode]={'argv':argv,'exit_code':result.returncode,'stdout':{'path':stdout_path.name,'bytes':len(result.stdout),'sha256':hashlib.sha256(result.stdout).hexdigest()},'stderr':{'path':stderr_path.name,'bytes':len(result.stderr),'sha256':hashlib.sha256(result.stderr).hexdigest()},'blocker_marker_seen':b'A05_NO_PIL_BLOCKER_ACTIVE' in result.stderr}
meta={'schema':'v15-cleanup-lazy-pil-a06-execution-v1','modes':records,'candidate_code_retries':0}
(root/'EXECUTION.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8'); print(json.dumps(meta))
