import copy, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile
root=pathlib.Path(__file__).resolve().parent; frozen=root/'frozen'; audit_path=frozen/'audit.py'; raw_path=frozen/'raw.json'; freeze_path=frozen/'FREEZE.json'; result_path=frozen/'audit.json'
spec=importlib.util.spec_from_file_location('frozen_audit',audit_path); audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
raw=json.loads(raw_path.read_text()); variants={}
x=copy.deepcopy(raw); x['events'].append({'event':'unexpected'}); variants['unexpected_event']=x
x=copy.deepcopy(raw); x['events'].insert(4,copy.deepcopy(next(e for e in x['events'] if e.get('event')=='stale_admission'))); variants['duplicate_stale']=x
x=copy.deepcopy(raw); next(e for e in x['events'] if e.get('event')=='stale_admission')['would_call_bridge']=True; variants['contradictory_bridge']=x
x=copy.deepcopy(raw); x['events'][2],x['events'][3]=x['events'][3],x['events'][2]; variants['reordered_transitions']=x
x=copy.deepcopy(raw); x['events'][0]['unexpected_field']=True; variants['unsupported_field']=x
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); result={'raw_sha256':digest(raw_path),'freeze_sha256':digest(freeze_path),'audit_source_sha256':digest(audit_path),'original_audit_sha256':digest(result_path),'baseline_errors':audit.errors_for(raw),'mutations':{k:audit.errors_for(v) for k,v in variants.items()}}
with tempfile.TemporaryDirectory() as d: cli=subprocess.run([sys.executable,str(audit_path),str(raw_path),'--freeze',str(freeze_path),'--output',str(pathlib.Path(d)/'audit.json')],capture_output=True,text=True)
result['cli']={'exit_code':cli.returncode,'stdout':cli.stdout,'stderr':cli.stderr}; print(json.dumps(result,indent=2,sort_keys=True))
if result['baseline_errors'] or any(result['mutations'].values()) or cli.returncode!=1: raise SystemExit(2)
