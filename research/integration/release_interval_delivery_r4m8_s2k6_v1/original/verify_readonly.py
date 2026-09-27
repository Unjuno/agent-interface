"""Revalidate retained bytes and decisions, never start a GUI/candidate run.

Run with: python -B verify_readonly.py
"""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    errors=[]
    unused_cache=ROOT/".verification-unused-pycache"
    if unused_cache.exists(): raise SystemExit("unexpected verification cache path")
    sys.dont_write_bytecode=True
    sys.pycache_prefix=str(unused_cache)
    manifest=json.loads((ROOT/'MANIFEST.json').read_text())
    for name,record in manifest['files'].items():
        p=ROOT/name
        if not p.is_file() or p.stat().st_size!=record['bytes'] or digest(p)!=record['sha256']:
            errors.append('manifest:'+name)
    freeze=json.loads((ROOT/'ANALYTICAL_FREEZE.json').read_text())
    for name,h in freeze['sha256'].items():
        if digest(ROOT/name)!=h: errors.append('analytical_freeze:'+name)
    upstream=json.loads((ROOT/'source/UPSTREAM.json').read_text())['files']
    for name,record in upstream.items():
        data=(ROOT/'source/upstream'/name).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=record['git_blob'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
            errors.append('upstream:'+name)
    # This audit parses already saved actor records and executes no backend.
    sys.path.insert(0,str(ROOT/'source'))
    from audit import audit_case,load_case
    old=json.loads((ROOT/'construction/AUDIT.json').read_text())
    fresh={cid:audit_case(load_case(ROOT/'construction'/cid),upstream) for cid in sorted(old)}
    if fresh!=old or any(v['errors'] for v in fresh.values()): errors.append('construction_audit')
    runs=[]
    commands=[
      ('finite_audit',['analysis_source/audit_intervals.py','verification/finite-first/RAW.json'],'verification/FINITE_AUDIT.json'),
      ('finite_controls',['analysis_source/interval_controls.py','verification/finite-first/RAW.json'],'verification/FINITE_CONTROLS.json'),
      ('construction_controls',['analysis_source/test_controls.py'],'verification/CONSTRUCTION_CONTROLS.json'),
      ('units',['-m','unittest','discover','-s','source','-p','test_witness.py','-v'],None)]
    for name,args,expected in commands:
        p=subprocess.run([sys.executable,'-B','-X','pycache_prefix='+str(unused_cache),*args],cwd=ROOT,capture_output=True,timeout=30)
        exact=expected is None or p.stdout==(ROOT/expected).read_bytes()
        runs.append({'name':name,'exit_code':p.returncode,'expected_stdout_byte_equal':exact})
        if p.returncode or not exact:errors.append('readonly_replay:'+name)
        if name=='units' and b'Ran 14 tests' not in p.stderr:errors.append('unit_count')
    stop=json.loads((ROOT/'PILOT_NOT_STARTED.json').read_text())
    if stop['live_pilot_cases']!=0:errors.append('pilot_boundary')
    if (ROOT/'FREEZE.json').exists() or (ROOT/'pilot').exists():errors.append('unexpected_live_allocation')
    result={'decision':'PASS_READONLY_RECONSTRUCTION' if not errors else 'FAIL_RECONSTRUCTION',
      'manifest_files':len(manifest['files']),'analytically_frozen_files':len(freeze['sha256']),
      'exact_upstream_modules':len(upstream),'construction_cases':len(fresh),
      'construction_audit_checks':sum(v['checks'] for v in fresh.values()),
      'readonly_commands':runs,'new_gui_trials':0,'new_finite_candidate_invocations':0,'errors':errors}
    print(json.dumps(result,indent=2,sort_keys=True));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
