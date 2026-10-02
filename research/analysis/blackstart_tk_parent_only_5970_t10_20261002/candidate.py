from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];APP=REPO/'research/analysis/blackstart_source_bound_5970_t3_20261001/derived/app.py';T9=REPO/'research/analysis/blackstart_tk_parent_window_5970_t9_20261002';RUNNER=T9/'runner.py';OUT=HERE/'run';RAW=HERE/'candidate.wrapper.raw.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wsl(p):return p.as_posix().replace('C:/','/mnt/c/')
def main():
    if OUT.exists() or RAW.exists():raise SystemExit('STOP_T10_OUTPUT_EXISTS')
    f=json.loads((HERE/'FREEZE.json').read_text());t9f=json.loads((T9/'FREEZE.json').read_text());apphash=sha(APP)
    if apphash!=f['t3_derived_app_sha256'] or sha(RUNNER)!=t9f['runner_sha256']:raise SystemExit('STOP_SHARED_SOURCE_HASH_MISMATCH')
    if sha(HERE/'candidate.py')!=f['candidate_sha256'] or sha(HERE/'observer.py')!=f['observer_sha256']:raise SystemExit('STOP_T10_SOURCE_HASH_MISMATCH')
    cmd=f"cd '{wsl(REPO)}' && xvfb-run -a -s '-screen 0 1024x768x24' python3 '{wsl(RUNNER)}' '{wsl(OUT)}' '{wsl(APP)}' '{wsl(HERE/'observer.py')}'"
    p=subprocess.run(['wsl.exe','-e','bash','-lc',cmd],capture_output=True,text=True,timeout=35)
    run=json.loads((OUT/'run.raw.json').read_text()) if (OUT/'run.raw.json').exists() else None
    obj={'schema':'blackstart-tk-parent-only-t10-wrapper-v1','app_sha256':apphash,'shared_runner_sha256':sha(RUNNER),'runner_exit_code':p.returncode,'stdout':p.stdout[-1500:],'stderr':p.stderr[-1500:],'run':run}
    RAW.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');return p.returncode
if __name__=='__main__':raise SystemExit(main())
