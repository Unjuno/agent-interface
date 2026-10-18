#!/usr/bin/env python3
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).parent.resolve();A09=ROOT.parent/"looming_yield_5905_image_only_t0_9_a09_20261005"
IMAGE="python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
def main():
    cmd=["docker","run","--pull=never","--rm","--network=none","--read-only","--tmpfs","/tmp:rw,noexec,nosuid,size=16m","--cap-drop=ALL","--security-opt=no-new-privileges","--cpus=1","--memory=1g","--mount",f"type=bind,src={A09/'candidate.py'},dst=/src/candidate.py,readonly",IMAGE,"python","-B","-c","from pathlib import Path; print('bytes='+str(Path('/src/candidate.py').stat().st_size))"]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    (ROOT/"preflight.stdout.txt").write_text(r.stdout);(ROOT/"preflight.stderr.txt").write_text(r.stderr)
    rec={"kind":"CONTAINER_PREFLIGHT_NOT_EXPERIMENT","command":cmd,"exit":r.returncode,"stdout":r.stdout,"stderr":r.stderr,"source_sha256":hashlib.sha256((A09/"candidate.py").read_bytes()).hexdigest(),"candidate_invocations":0,"auditor_invocations":0,"timestamp_utc":datetime.now(timezone.utc).isoformat()}
    (ROOT/"PREFLIGHT.json").write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n");print(json.dumps({"exit":r.returncode,"stdout":r.stdout.strip(),"stderr":r.stderr.strip()}))
    if r.returncode:raise SystemExit("STOP_CONTAINER_PREFLIGHT")
if __name__=="__main__":main()
