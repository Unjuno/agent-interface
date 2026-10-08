"""Create the A05 pre-candidate freeze once from the reviewed inputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = [
    "PLAN.md", "SOURCE_MANIFEST.json", "ENVIRONMENT.json", "SETUP.json",
    "SETUP_NOTES.md", "PRECHECK.json", "setup_check.py", "capture_environment.py",
    "candidate.py", "audit.py", "test_audit.py",
    "dependencies/input_owner_v10.py", "results/A05/setup.stdout.txt",
    "results/A05/setup.exit.txt", "results/A05/pre-freeze-tests.stdout.txt",
    "results/A05/pre-freeze-tests.exit.txt", "results/A05/pre-freeze-compile.exit.txt",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


freeze_path = HERE / "FREEZE.json"
if freeze_path.exists():
    raise FileExistsError(freeze_path)
source = json.loads((HERE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
environment = json.loads((HERE / "ENVIRONMENT.json").read_text(encoding="utf-8"))
report = {
    "schema": "v39-x11-event-routing-freeze-a05-v1",
    "allocation_id": "MAP01-V39-X11-EVENT-ROUTING-A05-20261004-01",
    "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
    "candidate_invocations_allowed": 1,
    "auditor_only_after_candidate_exit_zero": True,
    "retry_candidate_or_auditor": False,
    "decision": "PASS only when both routes have false/true/false server keymap, exactly one matching client KeyPress/KeyRelease and one counter increment; v10 explicit release is verified empty; Xvfb teardown is clean. Completed mismatch is FAIL; incomplete/custody error is STOP.",
    "candidate_sha256": sha(HERE / "candidate.py"),
    "auditor_sha256": sha(HERE / "audit.py"),
    "freeze_builder_sha256": sha(HERE / "build_freeze.py"),
    "precheck_sha256": sha(HERE / "PRECHECK.json"),
    "input_owner_v10_sha256": source["source_sha256"],
    "input_owner_v10_git_blob": source["git_blob"],
    "input_owner_v10_commit": source["source_commit"],
    "environment_machine_id": environment["orb_machine_id"],
    "environment": environment,
    "artifact_sha256": {name: sha(HERE / name) for name in FILES},
}
freeze_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"freeze_sha256": sha(freeze_path),
                  "candidate_sha256": report["candidate_sha256"],
                  "auditor_sha256": report["auditor_sha256"],
                  "artifact_count": len(report["artifact_sha256"])}, sort_keys=True))
