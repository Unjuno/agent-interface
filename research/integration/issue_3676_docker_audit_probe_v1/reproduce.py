import copy, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile
root=pathlib.Path(__file__).resolve().parent; frozen=root/'frozen'; audit_path=frozen/'audit.py'; raw_path=frozen/'raw.json'; freeze_path=frozen/'FREEZE.json'; result_path=frozen/'audit.json'
spec=importlib.util.spec_from_file_location('frozen_audit',audit_path); audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
raw=json.loads(raw_path.read_text()); variants={}
def add(name, change):
 x=copy.deepcopy(raw); change(x); variants[name]=x
add('mutate_xid',lambda r:r['events'][1]['identity'].__setitem__('xid',-1))
add('admit_stale',lambda r:next(e for e in r['events'] if e.get('event')=='stale_admission').__setitem__('admitted',True))
add('hide_emission',lambda r:next(e for e in r['events'] if e.get('event')=='fresh_positive_control')['click'].__setitem__('emissions',0))
add('unexpected_event',lambda r:r['events'].append({'event':'unexpected'}))
add('duplicate_stale',lambda r:r['events'].insert(4,copy.deepcopy(next(e for e in r['events'] if e.get('event')=='stale_admission'))))
add('contradictory_bridge',lambda r:next(e for e in r['events'] if e.get('event')=='stale_admission').__setitem__('would_call_bridge',True))
add('reordered_transitions',lambda r:r['events'].__setitem__(slice(2,4),list(reversed(r['events'][2:4]))))
add('missing_transition',lambda r:r['events'].__delitem__(2))
add('unsupported_field',lambda r:r['events'][0].__setitem__('unexpected_field',True))
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); result={'raw_sha256':digest(raw_path),'freeze_sha256':digest(freeze_path),'audit_source_sha256':digest(audit_path),'original_audit_sha256':digest(result_path),'baseline_errors':audit.errors_for(raw),'mutations':{k:audit.errors_for(v) for k,v in variants.items()}}
with tempfile.TemporaryDirectory() as d: cli=subprocess.run([sys.executable,str(audit_path),str(raw_path),'--freeze',str(freeze_path),'--output',str(pathlib.Path(d)/'audit.json')],capture_output=True,text=True)
result['cli']={'exit_code':cli.returncode,'stdout':cli.stdout,'stderr':cli.stderr}; print(json.dumps(result,indent=2,sort_keys=True))
if result['baseline_errors'] or any(result['mutations'].values()) or cli.returncode!=1: raise SystemExit(2)
