#!/usr/bin/env python3
"""Manifest committed post-run evidence using canonical Git blob bytes."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT_TEXT = "research/system1/typed_readout_decision_equivalence_1014_v3/formal"
ROOT = Path(ROOT_TEXT)
OUT = ROOT / "RESULTS_MANIFEST.json"
PREFIX = ROOT_TEXT + "/"


def git_blob(path: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", f"HEAD:{path}"])


paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", ROOT_TEXT], text=True).splitlines()
paths = sorted(p for p in paths if p.startswith(PREFIX) and p != str(OUT).replace("\\", "/"))
entries = []
for name in paths:
    payload = git_blob(name)
    entries.append({"path": name[len(PREFIX):], "bytes": len(payload),
                    "git_blob_sha1": subprocess.check_output(
                        ["git", "rev-parse", f"HEAD:{name}"], text=True).strip(),
                    "sha256": hashlib.sha256(payload).hexdigest()})
tree = hashlib.sha256("".join(f"{x['sha256']}  {x['path']}\n" for x in entries).encode()).hexdigest()
result = {"kind": "committed_formal_evidence_manifest", "canonical_bytes": "Git blob bytes at preceding evidence commit",
          "files": entries, "tree_sha256": tree}
OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(entries), "tree_sha256": tree}, sort_keys=True))
