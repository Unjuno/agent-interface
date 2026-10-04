import hashlib
import json
import platform
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[4]
paths = [
    "research/live_control/executor_v12.py",
    "research/live_control/executor_v5.py",
    "research/live_control/executor_v11.py",
    "research/live_control/lease_release_v1.py",
    "research/live_control/lease_cause_v2.py",
    "research/live_control/lease_cause_v1.py",
    "research/live_control/lease.py",
    "research/live_control/input_owner_v12.py",
    "research/live_control/test_executor_owner_cancel_cause_v1.py",
    "research/live_control/test_executor_v12.py",
]
manifest = {
    "schema": "map01-v39-cancel-release-cause-integration-v1",
    "classification": "local construction regression; not a formal allocation",
    "base_commit": "0757ae3d71314fecef6e055f619b680d34977fba",
    "python": platform.python_version(),
    "sources": {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in paths
    },
    "outputs": {
        name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
        for name in ("INTEGRATION-01.stdout.txt", "INTEGRATION-01.exit.txt",
                     "EXECUTOR-REGRESSION.stdout.txt", "EXECUTOR-REGRESSION.exit.txt")
    },
    "conclusion": "integration assertions pass; fake Xlib only",
}
(Path(__file__).parent / "SOURCE_MANIFEST.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2, sort_keys=True))
