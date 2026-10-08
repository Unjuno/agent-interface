from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
FILES = [
    "research/live_control/input_owner_v10.py",
    "research/live_control/input_owner_v12.py",
    "research/live_control/input_transition_owner_v3.py",
    "research/live_control/input_transition_owner_v4.py",
    "research/doom/doom_retained_input_backend_v4.py",
    "research/doom/doom_retained_input_backend_v5.py",
    "research/doom/session_map01_v13.py",
    "research/doom/session_map01_v14.py",
    "research/doom/MAP01_V14_CANCELLATION_RELEASE_CAUSE.md",
    "research/doom/results/map01-v39-cancel-release-cause-v1/README.md",
    "research/doom/results/map01-v39-cancel-release-cause-v1/make_source_manifest.py",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/README.md",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/FREEZE.json",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/test_cancel_release_cause.py",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/RED-01.stdout.txt",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/RED-01.exit.txt",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/RUN.json",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/audit_c01.py",
    "research/doom/results/map01-v39-cancel-release-cause-c01-20261004/AUDIT-01.json",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/README.md",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/FREEZE.json",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/FREEZE-CLARIFICATION.md",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/test_cancel_release_cause.py",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/CANDIDATE-01.stdout.txt",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/CANDIDATE-01.exit.txt",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/RUN.json",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/audit_c02.py",
    "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/AUDIT-01.json",
    "research/doom/results/map01-v39-cancel-release-cause-v1/backend-v4-regression.stdout.txt",
    "research/doom/results/map01-v39-cancel-release-cause-v1/backend-v4-regression.exit.txt",
    "research/doom/results/map01-v39-cancel-release-cause-v1/transition-v3-regression.stdout.txt",
    "research/doom/results/map01-v39-cancel-release-cause-v1/transition-v3-regression.exit.txt",
]
files = []
for relative in FILES:
    path = ROOT / relative
    content = path.read_bytes()
    blob = subprocess.check_output(["git", "-C", str(ROOT), "hash-object", str(path)], text=True).strip()
    files.append({"path": relative, "sha256": hashlib.sha256(content).hexdigest(),
                  "git_blob": blob, "bytes": len(content)})
head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
manifest = {"schema": "map01-v39-cancel-release-cause-source-manifest-v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit_at_generation": head,
            "experiment_source_commit": "8094af4631fc7bc5d92990e5151d5e89477ee39f",
            "files": files}
out = ROOT / "research/doom/results/map01-v39-cancel-release-cause-v1/SOURCE_MANIFEST.json"
out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
