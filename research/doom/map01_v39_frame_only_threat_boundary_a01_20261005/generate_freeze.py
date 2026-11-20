"""Create a single machine-bound freeze for this distinct synthetic stimulus."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
if (HERE/"FREEZE.json").exists(): raise SystemExit("freeze already exists")
source="research/doom/map01_overlap_controller_v39.py"
source_path=ROOT/source
freeze={"schema":"v39-frame-only-threat-boundary-freeze-v1",
        "source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "source_path":source,
        "source_git_blob":subprocess.check_output(["git","hash-object",str(source_path)],cwd=ROOT,text=True).strip(),
        "source_sha256":hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "input_path":"research/doom/map01_v39_frame_only_threat_boundary_a01_20261005/input.json",
        "input_sha256":hashlib.sha256((HERE/"input.json").read_bytes()).hexdigest(),
        "candidate_invocations":1,"auditor_invocations":1,"retries":0,
        "live_game":False,"model_calls":0,"gui":False,"os_input":False,"real_x_server":False}
(HERE/"FREEZE.json").write_text(json.dumps(freeze,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(freeze,sort_keys=True))
