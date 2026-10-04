import hashlib
import json
import subprocess
import sys
from pathlib import Path

source = Path(__file__).resolve().parent
freeze_path = (source / sys.argv[1]).resolve()
freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
errors = []
for name, expected in freeze["source_files_sha256"].items():
    data = (source / name).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        errors.append(f"SHA256 {name}: expected {expected}, got {actual}")
for name, expected in freeze["source_git_blobs"].items():
    actual = subprocess.check_output(["git", "hash-object", "--no-filters", str(source / name)], text=True).strip()
    if actual != expected:
        errors.append(f"Git blob {name}: expected {expected}, got {actual}")
if errors:
    raise SystemExit("FAIL_SOURCE_PREFLIGHT\n" + "\n".join(errors))
print(f"PASS_SOURCE_PREFLIGHT source_files={len(freeze['source_files_sha256'])} git_blobs={len(freeze['source_git_blobs'])}")
print(f"freeze={freeze_path}")
print(f"source_main_base={freeze['source_main_base']}")
