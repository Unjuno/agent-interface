from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[2]; T3=REPO/'research/analysis/blackstart_source_bound_5970_t3_20261001/derived'; OUT=HERE/'run'; RAW=HERE/'candidate.wrapper.raw.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wsl(p):return p.as_posix().replace('C:/','/mnt/c/')
def main():
    if OUT.exists() or RAW.exists():raise SystemExit('STOP_T6_ONE_SHOT_OUTPUT_EXISTS')
    freeze=json.loads((HERE/'FREEZE.json').read_text()); app=T3/'app.py'; actual=sha(app)
    if actual!=freeze['t3_derived_app_sha256']:raise SystemExit('STOP_T3_APP_HASH_MISMATCH')
    for name,key in [('candidate.py','candidate_sha256'),('runner.py','runner_sha256'),('observer.py','observer_sha256')]:
        if sha(HERE/name)!=freeze[key]:raise SystemExit('STOP_FROZEN_T6_SOURCE_MISMATCH:'+name)
    cmd=f"cd '{wsl(REPO)}' && xvfb-run -a -s '-screen 0 1024x768x24' python3 '{wsl(HERE/'runner.py')}' '{wsl(OUT)}' '{wsl(app)}' '{wsl(HERE/'observer.py')}'"
    p=subprocess.run(['wsl.exe','-e','bash','-lc',cmd],capture_output=True,text=True,timeout=35)
    result={'schema':'blackstart-allwindow-trace-t6-wrapper-v1','app_sha256':actual,'runner_exit_code':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'run':json.loads((OUT/'run.raw.json').read_text()) if (OUT/'run.raw.json').exists() else None}
    RAW.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return p.returncode
if __name__=='__main__':raise SystemExit(main())
