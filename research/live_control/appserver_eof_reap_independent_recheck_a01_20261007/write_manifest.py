#!/usr/bin/env python3
"""Write hashes for the frozen recheck report, runner, and raw outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
FILES = [
    "README.md",
    "audit-attempt-v1-failure.txt",
    "audit_recheck.py",
    "frozen_test.py",
    "raw/base.txt",
    "raw/candidate.txt",
    "RESULT.json",
    "run_independent_recheck.py",
    "write_manifest.py",
]


def main() -> int:
    entries = []
    for relative in FILES:
        data = (HERE / relative).read_bytes()
        entries.append({
            "path": relative,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    manifest = {
        "format": "appserver-eof-reap-independent-recheck-manifest-v1",
        "base_commit": "9fb2dd6782d1d1477a00d14be870487fd4c54fa2",
        "candidate_commit": "c6f5a122afee85e44bec5c39b80f02e6b939d56a",
        "files": entries,
    }
    (HERE / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"MANIFEST_OK files={len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
