from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
T3=REPO/'research/analysis/blackstart_source_bound_5970_t3_20261001'
OUT=HERE/'run'; RAW=HERE/'candidate.raw.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def wsl(p): return p.as_posix().replace('C:/','/mnt/c/')
def main():
    if OUT.exists() or RAW.exists(): raise SystemExit('STOP_T4_ONE_SHOT_OUTPUT_EXISTS')
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    expected={'app.py':freeze['t3_derived_app_sha256'],'observer.py':freeze['t3_derived_observer_sha256']}
    for name,digest in expected.items():
        if sha(T3/'derived'/name)!=digest: raise SystemExit('STOP_T3_DERIVED_HASH:'+name)
    archive=subprocess.check_output(['git','show',f"{freeze['upstream_source_commit']}:research/integration/x11_reconnect_key_state_2107_v1/EVIDENCE_BASE64.json"])
    meta=json.loads(archive)
    if meta.get('archive_sha256')!=freeze['upstream_archive_sha256']: raise SystemExit('STOP_ARCHIVE_IDENTITY')
    for name,expected_hash in (('app.py','fe24b580beaf048921352cc49ec380ba6f3122240c9197a1b62fc766d72afa63'),('observer.py','a3e46223019f67bf98bb2a202aa24196628d2c975255bec034bd7855bf812d4d')):
        if sha(T3/'derived'/name)!=expected_hash: raise SystemExit('STOP_T3_HASH:'+name)
    cmd=f"cd '{wsl(REPO)}' && xvfb-run -a -s '-screen 0 1024x768x24' python3 '{wsl(HERE/'runner.py')}' '{wsl(OUT)}' '{wsl(T3/'derived/app.py')}' '{wsl(T3/'derived/observer.py')}'"
    p=subprocess.run(['wsl.exe','-e','bash','-lc',cmd],capture_output=True,text=True,timeout=30)
    run=json.loads((OUT/'run.raw.json').read_text()) if (OUT/'run.raw.json').exists() else None
    result={'schema':'blackstart-xrecord-t4-candidate-v1','verified_derived_sha256':{n:sha(T3/'derived'/n) for n in expected},'archive_sha256':meta['archive_sha256'],'runner_exit_code':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'run':run}
    RAW.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return p.returncode
if __name__=='__main__': raise SystemExit(main())
