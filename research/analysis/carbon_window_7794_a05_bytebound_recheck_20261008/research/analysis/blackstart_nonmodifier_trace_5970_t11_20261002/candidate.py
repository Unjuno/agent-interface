from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];APP=REPO/'research/analysis/blackstart_source_bound_5970_t3_20261001/derived/app.py';OBS=REPO/'research/analysis/blackstart_tk_parent_only_5970_t10_20261002/observer.py';OUT=HERE/'run';RAW=HERE/'candidate.wrapper.raw.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wsl(p):return p.as_posix().replace('C:/','/mnt/c/')
def main():
    if OUT.exists() or RAW.exists():raise SystemExit('STOP_T11_OUTPUT_EXISTS')
    f=json.loads((HERE/'FREEZE.json').read_text());t10=json.loads((REPO/'research/analysis/blackstart_tk_parent_only_5970_t10_20261002/FREEZE.json').read_text())
    if sha(APP)!=f['t3_derived_app_sha256'] or sha(OBS)!=f['t10_parent_only_observer_sha256']:raise SystemExit('STOP_SHARED_SOURCE_HASH_MISMATCH')
    for n,k in [('candidate.py','candidate_sha256'),('runner.py','runner_sha256')]:
        if sha(HERE/n)!=f[k]:raise SystemExit('STOP_T11_SOURCE_HASH_MISMATCH:'+n)
    cmd=f"cd '{wsl(REPO)}' && xvfb-run -a -s '-screen 0 1024x768x24' python3 '{wsl(HERE/'runner.py')}' '{wsl(OUT)}' '{wsl(APP)}' '{wsl(OBS)}'"
    p=subprocess.run(['wsl.exe','-e','bash','-lc',cmd],capture_output=True,text=True,timeout=35)
    run=json.loads((OUT/'run.raw.json').read_text()) if (OUT/'run.raw.json').exists() else None
    obj={'schema':'blackstart-nonmodifier-trace-t11-wrapper-v1','app_sha256':sha(APP),'observer_sha256':sha(OBS),'runner_exit_code':p.returncode,'stdout':p.stdout[-1500:],'stderr':p.stderr[-1500:],'run':run}
    RAW.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');return p.returncode
if __name__=='__main__':raise SystemExit(main())
