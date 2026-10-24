import hashlib,json,os,subprocess,sys,time
from pathlib import Path
OUT=Path('/out'); LOCK=Path('/wheels/requirements-s15-cp312.lock'); MANIFEST=Path('/wheels/WHEELHOUSE-SHA256.json')
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
for f in manifest['files']:
 p=Path('/wheels')/f['name']; assert p.is_file() and p.stat().st_size==f['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'], 'wheel hash mismatch '+f['name']
assert len(manifest['files'])==31
install=[sys.executable,'-m','pip','install','--no-index','--no-deps','--find-links=/wheels','--target=/tmp/s16-deps','-r',str(LOCK)]
env=os.environ.copy(); env['PYTHONPATH']='/tmp/s16-deps:/src'; env['AGENT_INTERFACE_FAKE_X_COMPOSITION_RAW_DIR']='/out/fake-x-raw'; env['PYTHONDONTWRITEBYTECODE']='1'
t=time.monotonic(); ins=subprocess.run(install,text=True,capture_output=True,timeout=60); (OUT/'pip-install.stdout.txt').write_text(ins.stdout,encoding='utf-8'); (OUT/'pip-install.stderr.txt').write_text(ins.stderr,encoding='utf-8')
if ins.returncode: save('result.json',{'status':'FAIL_OR_UNKNOWN','stage':'offline_install','exit_code':ins.returncode,'python':sys.version,'wheel_count':len(manifest['files'])}); sys.exit(70)
case='runtime.cli_v1.test_mcp_relay_composition.StandardMCPRelayCompositionTests.test_generation_change_refuses_before_any_relay_action'
t0=time.monotonic(); p=subprocess.run([sys.executable,'-B','-m','unittest','-v',case],cwd='/src',env=env,text=True,capture_output=True,timeout=90); elapsed=time.monotonic()-t0
(OUT/'test.stdout.txt').write_text(p.stdout,encoding='utf-8'); (OUT/'test.stderr.txt').write_text(p.stderr,encoding='utf-8')
raw=OUT/'fake-x-raw'; files=sorted(raw.glob('*')) if raw.exists() else []
rows=[{'name':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files if f.is_file()]
(OUT/'fake-x-raw-manifest.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n',encoding='utf-8')
status='PASS_FAKE_X_TARGET_GENERATION_REFUSAL_SCOPED' if p.returncode==0 and 'Ran 1 test' in p.stderr and 'OK' in p.stderr and any(f.name=='target-generation-refusal.json' for f in files) else 'FAIL_OR_UNKNOWN'
save('result.json',{'status':status,'python':sys.version,'platform':sys.platform,'test_selector':case,'exit_code':p.returncode,'elapsed_seconds':elapsed,'test_stderr_sha256':hashlib.sha256(p.stderr.encode()).hexdigest(),'wheel_count':len(manifest['files']),'raw_file_count':len(rows),'raw_manifest_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),'scope':'synthetic Fake X only','task_success':None,'replay':'denied','network':'disabled in container'})
sys.exit(0 if status=='PASS_FAKE_X_TARGET_GENERATION_REFUSAL_SCOPED' else 1)
