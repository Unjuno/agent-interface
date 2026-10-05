"""Verify that an evidence manifest names exactly the present files and hashes."""
import hashlib
import json
import os
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: verify_evidence_manifest.py EVIDENCE_DIRECTORY")
root = Path(sys.argv[1]).resolve()
manifest_path = root / "evidence-manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
expected = manifest.get("files")
if not isinstance(expected, dict):
    raise SystemExit("manifest files map missing")
actual_paths = set()
for current, directories, filenames in os.walk(root, followlinks=False):
    current_path = Path(current)
    for name in list(directories):
        path = current_path / name
        if path.is_symlink():
            directories.remove(name)
            actual_paths.add(str(path.relative_to(root)))
    for name in filenames:
        path = current_path / name
        if path != manifest_path:
            actual_paths.add(str(path.relative_to(root)))
missing_from_manifest = sorted(actual_paths - set(expected))
missing_on_disk = sorted(name for name in set(expected) - actual_paths
                         if not (expected[name].get("type") == "symlink"
                                 and not (root / name).exists()
                                 and not (root / name).is_symlink()
                                 and (root / name).parent == root / "broker-repo"))
if missing_from_manifest or missing_on_disk:
    raise SystemExit(json.dumps({"missing_from_manifest": missing_from_manifest,
                                 "missing_on_disk": missing_on_disk}))
for name, expected_hash in expected.items():
    path = root / name
    if expected_hash.get("type") == "symlink":
        okay = ((path.is_symlink() and os.readlink(path) == expected_hash.get("target"))
                or (not path.exists() and not path.is_symlink()
                    and path.parent == root / "broker-repo"
                    and isinstance(expected_hash.get("target"), str)))
    elif expected_hash.get("type") == "file":
        okay = (path.is_file() and not path.is_symlink()
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash.get("sha256"))
    else:
        okay = False
    if not okay: raise SystemExit(f"entry mismatch: {name}")
print(f"evidence integrity {len(expected)}/{len(expected)} PASS")
