#!/usr/bin/env python3
"""Fail-closed source manifest verifier; performs no experiment actions."""

import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parents[3]
freeze_path = Path(__file__).with_name("FREEZE.json")
freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
errors = []
for relative, expected in freeze["sha256"].items():
    path = root / relative
    if not path.is_file():
        errors.append(f"missing:{relative}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        errors.append(f"hash:{relative}")
print(json.dumps({"status": "PASS" if not errors else "STOP_SOURCE_MISMATCH",
                  "base_commit": freeze["base_commit"], "checked": len(freeze["sha256"]),
                  "errors": errors}, sort_keys=True))
if errors:
    raise SystemExit(2)
