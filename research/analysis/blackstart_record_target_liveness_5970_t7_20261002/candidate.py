from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];APP=REPO/'research/analysis/blackstart_source_bound_5970_t3_20261001/derived/app.py';OUT=HERE/'run';RAW=HERE/'candidate.wrapper.raw.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wsl(p):return p.as_posix().replace('C:/','/mnt/c/')
def main():
    if OUT.exists() or RAW.exists():raise SystemExit('STOP_T7_OUTPUT_EXISTS')
    f=json.loads((HERE/'FREEZE.json').read_text());actual=sha(APP)
    if actual!=f['t3_derived_app_sha256']:raise SystemExit('STOP_T3_APP_HASH_MISMATCH')
    if sha(HERE/'candidate.py')!=f['candidate_sha256'] or sha(HERE/'runner.py')!=f['runner_sha256']:raise SystemExit('STOP_T7_SOURCE_HASH_MISMATCH')
    cmd=f"cd '{wsl(REPO)}' && xvfb-run -a -s '-screen 0 1024x768x24' python3 '{wsl(HERE/'runner.py')}' '{wsl(OUT)}' '{wsl(APP)}' '{f['recorded_target_xid']}'"
    p=subprocess.run(['wsl.exe','-e','bash','-lc',cmd],capture_output=True,text=True,timeout=30)
    obj=json.loads((OUT/'candidate.raw.json').read_text()) if (OUT/'candidate.raw.json').exists() else None
    result={'schema':'blackstart-record-target-liveness-t7-wrapper-v1','app_sha256':actual,'runner_exit_code':p.returncode,'stdout':p.stdout[-1500:],'stderr':p.stderr[-1500:],'candidate':obj}
    RAW.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return p.returncode
if __name__=='__main__':raise SystemExit(main())
