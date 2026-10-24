import hashlib,json,os,subprocess,sys,time
from pathlib import Path
OUT=Path('/out'); LOCK=Path('/wheels/requirements-s12-cp314.lock'); MANIFEST=Path('/wheels/WHEELHOUSE-SHA256.json')
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
for f in manifest['files']:
 p=Path('/wheels')/f['name']; assert p.is_file() and p.stat().st_size==f['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'], 'wheel hash mismatch '+f['name']
assert len(manifest['files'])==30, 'unexpected wheel count'
install=[sys.executable,'-m','pip','install','--no-index','--no-deps','--find-links=/wheels','--target=/tmp/s12-deps','-r',str(LOCK)]
env=os.environ.copy(); env['PYTHONPATH']='/tmp/s12-deps:/src'; env['PYTHONDONTWRITEBYTECODE']='1'
t=time.monotonic(); ins=subprocess.run(install,text=True,capture_output=True,timeout=60); (OUT/'pip-install.stdout.txt').write_text(ins.stdout,encoding='utf-8'); (OUT/'pip-install.stderr.txt').write_text(ins.stderr,encoding='utf-8')
if ins.returncode: save('result.json',{'status':'FAIL_OR_UNKNOWN','stage':'offline_install','exit_code':ins.returncode,'python':sys.version,'wheel_count':len(manifest['files'])}); sys.exit(70)
case='runtime.cli_v1.test_mcp_relay_composition.StandardMCPRelayCompositionTests.test_standard_owned_caller_holds_fake_x_reply_and_cancels_fail_closed'
cmd=[sys.executable,'-B','-m','unittest','-v',case]; t0=time.monotonic(); p=subprocess.run(cmd,cwd='/src',env=env,text=True,capture_output=True,timeout=90); elapsed=time.monotonic()-t0
(OUT/'test.stdout.txt').write_text(p.stdout,encoding='utf-8'); (OUT/'test.stderr.txt').write_text(p.stderr,encoding='utf-8')
status='PASS_FAKE_X_STANDARD_CALLER_SCOPED' if p.returncode==0 and 'Ran 1 test' in p.stderr and 'OK' in p.stderr else 'FAIL_OR_UNKNOWN'
save('result.json',{'status':status,'python':sys.version,'platform':sys.platform,'test_selector':case,'exit_code':p.returncode,'elapsed_seconds':elapsed,'test_stdout_sha256':hashlib.sha256(p.stdout.encode()).hexdigest(),'test_stderr_sha256':hashlib.sha256(p.stderr.encode()).hexdigest(),'wheel_count':len(manifest['files']),'release_claim':'UNKNOWN; synthetic Fake X only','task_success':None,'replay':'denied','network':'disabled in container'})
sys.exit(0 if status=='PASS_FAKE_X_STANDARD_CALLER_SCOPED' else 1)
