from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[2]
T3=REPO/'research/analysis/blackstart_source_bound_5970_t3_20261001/derived'
OUT=HERE/'run'; RAW=HERE/'candidate.wrapper.raw.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wsl(p):return p.as_posix().replace('C:/','/mnt/c/')
def main():
    if OUT.exists() or RAW.exists():raise SystemExit('STOP_T5_ONE_SHOT_OUTPUT_EXISTS')
    freeze=json.loads((HERE/'FREEZE.json').read_text()); expected={'app.py':freeze['t3_derived_app_sha256'],'observer.py':freeze['t3_derived_observer_sha256']}
    actual={n:sha(T3/n) for n in expected}
    if actual!=expected:raise SystemExit('STOP_T3_DERIVED_HASH_MISMATCH')
    cmd=f"cd '{wsl(REPO)}' && xvfb-run -a -s '-screen 0 1024x768x24' python3 '{wsl(HERE/'runner.py')}' '{wsl(OUT)}' '{wsl(T3/'app.py')}'"
    p=subprocess.run(['wsl.exe','-e','bash','-lc',cmd],capture_output=True,text=True,timeout=30)
    result={'schema':'blackstart-xevent-target-t5-wrapper-v1','derived_sha256':actual,'runner_exit_code':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'candidate':json.loads((OUT/'candidate.raw.json').read_text()) if (OUT/'candidate.raw.json').exists() else None}
    RAW.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return p.returncode
if __name__=='__main__':raise SystemExit(main())
