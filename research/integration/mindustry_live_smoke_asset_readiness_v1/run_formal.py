#!/usr/bin/env python3
import hashlib, importlib, json, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def load(n): return json.loads((ROOT/n).read_text())
def dump(n,v): (ROOT/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def inspect_file(paths, expected_sha, expected_bytes=None):
    observations=[]
    for raw in paths:
        p=Path(raw)
        if not p.is_file(): continue
        row={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
        row['identity_ok']=row['sha256']==expected_sha and (expected_bytes is None or row['bytes']==expected_bytes)
        observations.append(row)
    return observations

def main():
    sentinel=ROOT/'.formal-invoked'
    if sentinel.exists() or (ROOT/'RESULT.json').exists(): raise SystemExit('formal already invoked')
    sentinel.write_text('1\n')
    f=load('fixture.json')
    jar=f['jar']
    provenance={
      'jar_digest_match':jar['repo_sha256']==jar['official_sha256'],
      'jar_size_match':jar['repo_bytes']==jar['official_bytes'],
      'jar_url_matches_official':jar['repo_url'].endswith('/v160.2/Mindustry.jar'),
      'save_identity_declared':len(f['save']['git_blob'])==40 and len(f['save']['sha256'])==64
    }
    commands={name:shutil.which(name) for name in f['required_commands']}
    modules={}
    for name in f['required_python_modules']:
        try:
            mod=importlib.import_module(name); modules[name]={'available':True,'version':str(getattr(mod,'__version__',''))}
        except Exception as e: modules[name]={'available':False,'error':type(e).__name__}
    try:
        java=subprocess.run(['java','-version'],text=True,capture_output=True,timeout=5)
        java_text=(java.stderr or java.stdout).splitlines()[0] if (java.stderr or java.stdout) else ''
    except Exception as e: java_text=type(e).__name__
    env_ok=all(commands.values()) and all(v['available'] for v in modules.values()) and ('21.' in java_text or 'version "21' in java_text)
    jar_obs=inspect_file(f['candidate_jar_paths'],jar['repo_sha256'],jar['repo_bytes'])
    save_obs=inspect_file(f['candidate_save_paths'],f['save']['sha256'])
    jar_ready=any(x['identity_ok'] for x in jar_obs); save_ready=any(x['identity_ok'] for x in save_obs)
    if not all(provenance.values()): decision='FAIL_PROVENANCE_MISMATCH'
    elif not env_ok: decision='HOLD_ENVIRONMENT_MISSING'
    elif jar_ready and save_ready: decision='PASS_ASSETS_READY'
    else: decision='HOLD_ASSETS_NOT_MATERIALIZED'
    out={'schema':'mindustry_live_smoke_asset_readiness_result_v1','task':f['task'],'formal_invocation':1,'formal_reruns':0,
         'decision':decision,'provenance':provenance,'commands':commands,'modules':modules,'java':java_text,'environment_ok':env_ok,
         'jar_observations':jar_obs,'save_observations':save_obs,'jar_ready':jar_ready,'save_ready':save_ready,
         'scope':'asset/environment readiness only; no GUI/game/model/live result'}
    dump('RESULT.json',out); print(json.dumps({'decision':decision,'environment_ok':env_ok,'jar_ready':jar_ready,'save_ready':save_ready},sort_keys=True))
    raise SystemExit(1 if decision.startswith('FAIL_') else 0)
if __name__=='__main__': main()
