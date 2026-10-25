"""Write a deterministic SHA-256 manifest for an experiment evidence tree."""
import hashlib
import json
import os
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: seal_evidence.py EVIDENCE_DIRECTORY")
root = Path(sys.argv[1]).resolve()
manifest = root / "evidence-manifest.json"
previous = (json.loads(manifest.read_text(encoding="utf-8")).get("files", {})
            if manifest.is_file() else {})
rows = {}
for current, directories, filenames in os.walk(root, followlinks=False):
    current_path = Path(current)
    for name in list(directories):
        path = current_path / name
        if path.is_symlink():
            directories.remove(name)
            rows[str(path.relative_to(root))] = {"type": "symlink",
                                                "target": os.readlink(path)}
    for name in filenames:
        path = current_path / name
        if path == manifest:
            continue
        if path.is_symlink():
            rows[str(path.relative_to(root))] = {"type": "symlink",
                                                "target": os.readlink(path)}
        else:
            rows[str(path.relative_to(root))] = {"type": "file",
                                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
for name, record in previous.items():
    path = root / name
    if (record.get("type") == "symlink" and not path.exists()
            and not path.is_symlink() and path.parent == root / "broker-repo"):
        rows[name] = record
manifest.write_text(json.dumps({"schema": "issue3311-evidence-manifest-v1",
                                "files": rows}, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
print(f"sealed {len(rows)} files in {manifest}")
