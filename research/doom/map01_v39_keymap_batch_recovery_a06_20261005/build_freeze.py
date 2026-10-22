import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCES = [
    "research/doom/session_map01_v15.py",
    "research/doom/doom_owner_thread_release_batch_backend_v1.py",
    "research/doom/doom_typed_release_backend_v2.py",
    "research/live_control/input_transition_owner_v4.py",
    "research/live_control/input_transition_owner_v3.py",
    "research/live_control/input_owner_v12.py",
]
ARTIFACTS = ["PREREGISTRATION.md", "README.md", "candidate.py", "audit.py", "run_candidate.py"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
if commit != "5a290af598e4ef365ac5dfe66dca2c3c9916a20a":
    raise SystemExit("STOP_MAIN_COMMIT_MISMATCH")
freeze = {
    "schema": "v39-keymap-batch-recovery-a06-freeze-v1",
    "main_commit": commit,
    "source_sha256": {p: sha(ROOT / p) for p in SOURCES},
    "artifact_sha256": {p: sha(HERE / p) for p in ARTIFACTS},
    "candidate_invocations": 1,
    "scenario_count": 3,
    "scope": "fake Xlib V39 release-batch composition; no live game or physical input",
}
out = HERE / "FREEZE.json"
if out.exists():
    raise SystemExit("STOP_FREEZE_ALREADY_EXISTS")
out.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
print(json.dumps({"freeze": str(out), "main_commit": commit, "sources": len(SOURCES)}))
