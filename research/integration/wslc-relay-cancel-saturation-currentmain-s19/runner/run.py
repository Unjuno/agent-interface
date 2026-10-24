import hashlib,json,os,subprocess,sys,time,traceback
from pathlib import Path
OUT=Path('/out'); LOCK=Path('/wheels/requirements-cp312.lock'); MANIFEST=Path('/wheels/WHEELHOUSE-SHA256.json')
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
try:
 manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
 if len(manifest['files'])!=31: raise RuntimeError('wheel manifest count mismatch')
 for f in manifest['files']:
  p=Path('/wheels')/f['name']
  if not p.is_file() or p.stat().st_size!=f['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']: raise RuntimeError('wheel hash mismatch: '+f['name'])
 install=[sys.executable,'-m','pip','install','--no-index','--no-deps','--find-links=/wheels','--target=/tmp/s19-deps','-r',str(LOCK)]
 env=os.environ.copy();env['PYTHONPATH']='/tmp/s19-deps:/src';env['AGENT_INTERFACE_RELAY_CANCEL_COMPOSITION_RAW_DIR']='/out/raw';env['PYTHONDONTWRITEBYTECODE']='1'
 start=time.monotonic();ins=subprocess.run(install,text=True,capture_output=True,timeout=60)
 (OUT/'pip-install.stdout.txt').write_text(ins.stdout,encoding='utf-8');(OUT/'pip-install.stderr.txt').write_text(ins.stderr,encoding='utf-8')
 if ins.returncode: save('result.json',{'status':'FAIL_OR_UNKNOWN','stage':'offline_install','exit_code':ins.returncode,'python':sys.version,'wheel_count':len(manifest['files'])});sys.exit(70)
 case='runtime.cli_v1.test_mcp_relay_composition.StandardMCPRelayCompositionTests.test_saturated_relay_stdout_dispatches_cancel_to_held_fake_x_caller'
 t0=time.monotonic();p=subprocess.run([sys.executable,'-B','-m','unittest','-v',case],cwd='/src',env=env,text=True,capture_output=True,timeout=90);elapsed=time.monotonic()-t0
 (OUT/'test.stdout.txt').write_text(p.stdout,encoding='utf-8');(OUT/'test.stderr.txt').write_text(p.stderr,encoding='utf-8')
 raw=OUT/'raw';files=sorted(x for x in raw.glob('*') if x.is_file()) if raw.exists() else []
 rows=[{'name':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
 (OUT/'raw-manifest.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 status='PASS_FAKE_X_RELAY_COMPOSITION_ONLY' if p.returncode==0 and 'Ran 1 test' in p.stderr and 'OK' in p.stderr and any(f.name=='result.json' for f in files) else 'FAIL_OR_UNKNOWN'
 save('result.json',{'status':status,'python':sys.version,'platform':sys.platform,'test_selector':case,'exit_code':p.returncode,'elapsed_seconds':elapsed,'raw_file_count':len(rows),'raw_manifest_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),'scope':'synthetic Fake X standard relay/caller composition only','task_success':None,'replay':'denied','network':'disabled inside container','wheel_count':len(manifest['files'])})
 sys.exit(0 if status=='PASS_FAKE_X_RELAY_COMPOSITION_ONLY' else 1)
except Exception as exc:
 save('runner-exception.json',{'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()});raise

