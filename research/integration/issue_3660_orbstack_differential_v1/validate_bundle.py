#!/usr/bin/env python3
"""Verify the raw and frozen research-code hashes in SOURCE_MANIFEST.json."""
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "SOURCE_MANIFEST.json").read_text())
errors = []
for rel, expected in manifest["files"].items():
    path = root / rel
    if not path.is_file():
        errors.append(f"missing:{rel}")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        errors.append(f"sha256_mismatch:{rel}")
raw = root / "evidence/frozen_3652_formal01_raw.json"
if hashlib.sha256(raw.read_bytes()).hexdigest() != manifest["frozen_raw_sha256"]:
    errors.append("frozen_raw_sha256_mismatch")
result = {"decision": "PASS_BUNDLE_INTEGRITY" if not errors else "FAIL_BUNDLE_INTEGRITY",
          "file_count": len(manifest["files"]), "errors": errors,
          "frozen_raw_sha256": manifest["frozen_raw_sha256"]}
print(json.dumps(result, sort_keys=True, indent=2))
if errors:
    raise SystemExit(1)
