#!/usr/bin/env python3
"""Verify the public #7316 capsule and re-audit saved outputs only.

No archived candidate, server, driver, or experiment source is executed.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
sha256 = lambda value: hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


manifest = json.loads((ROOT / "MANIFEST.json").read_bytes())
require(manifest["scope"] == "inert archive data, no actors executed on import/discovery", "unexpected outer scope")
for name, expected in manifest["members"].items():
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts, f"unsafe outer path: {name}")
    data = (ROOT / Path(*path.parts)).read_bytes()
    require(len(data) == expected["bytes"] and sha256(data) == expected["sha256"], f"outer hash mismatch: {name}")

domains = json.loads((ROOT / "PUBLIC_DOMAINS.json").read_bytes())
capsule_bytes = (ROOT / "evidence.json.gz").read_bytes()
require(sha256(capsule_bytes) == manifest["members"]["evidence.json.gz"]["sha256"], "capsule hash mismatch")
capsule = json.loads(gzip.decompress(capsule_bytes))
require(capsule["scope"] == "inert own native receiver restart evidence; explicit private original/public domains", "unexpected capsule scope")
members = capsule["members"]
require(len(members) == 69, "unexpected capsule member count")
projection_path = "original_restart/second.stderr"
expected_projection = {
    "original_bytes": 355,
    "original_sha256": "52476de8a561ad76b10f947e6cfaf03507bcdf1b18bc9bfda0edc522db3014c2",
    "public_bytes": 286,
    "public_sha256": "89d3dd4c89b2cbaae95bd0dc7dd4b68b6c85113ad1455c0935c8ff538ca0b8ed",
    "projection": "own path text projection only; private-original receipt hash not public stream hash",
}
require(domains[projection_path] == expected_projection, "documented projection domain changed")

with tempfile.TemporaryDirectory(prefix="http-receiver-public-recheck-") as temp:
    root = Path(temp)
    for name, entry in members.items():
        path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts, f"unsafe capsule path: {name}")
        data = base64.b64decode(entry["base64"], validate=True)
        require(len(data) == entry["bytes"] and sha256(data) == entry["sha256"], f"capsule member mismatch: {name}")
        output = root.joinpath(*path.parts)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    (root / "PUBLIC_DOMAINS.json").write_bytes((ROOT / "PUBLIC_DOMAINS.json").read_bytes())
    for name in ("server.py", "driver.py", "run_once.py", "capture_v2.py", "read_saved.py"):
        public = (ROOT / "source" / f"{name}.txt").read_bytes()
        require((root / name).read_bytes() == public, f"public source projection mismatch: {name}")

    reader_path = root / "read_saved.py"
    reader = reader_path.read_text(encoding="utf-8")
    original = "for k,v in r['streams'].items():b=(root/(phase+'.'+k)).read_bytes();assert len(b)==v['bytes'] and sha(b)==v['sha256']"
    projected = """for k,v in r['streams'].items():
            b=(root/(phase+'.'+k)).read_bytes()
            if name=='original_restart' and phase=='second' and k=='stderr':
                public=json.loads((P/'PUBLIC_DOMAINS.json').read_bytes())[name+'/second.stderr']
                assert v['bytes']==public['original_bytes'] and v['sha256']==public['original_sha256']
                assert len(b)==public['public_bytes'] and sha(b)==public['public_sha256']
            else:
                assert len(b)==v['bytes'] and sha(b)==v['sha256']"""
    require(reader.count(original) == 1, "saved reader assertion anchor missing or ambiguous")
    safe_reader = root / "read_saved_public_projection.py"
    safe_reader.write_text(reader.replace(original, projected), encoding="utf-8")
    run = subprocess.run([sys.executable, str(safe_reader)], cwd=root, capture_output=True, text=True, timeout=30)
    require(run.returncode == 0, f"saved-only audit failed: {run.stderr[-2000:]}")
    output = run.stdout.strip().splitlines()[-1]
    result = json.loads(output)

require(result["status"] == "QUALIFIED_NATIVE_WINDOWS_RECEIVER_RESTART_CONSTRUCTION", "unexpected saved audit status")
require(result["rejected_copied_contradictions"] == ["false_first_ack", "false_double_effect", "false_conflict_success", "unreaped_first"], "mutation controls differ")
require(result["source_identity_verified"] and result["full_saved_db_wal_shm_views_joined"] and result["source_and_original_raw_unchanged"], "saved audit integrity gate failed")
require(result["model_calls"] == 0 and result["old_formal_or_browser_replay"] is False and result["subject_replay_in_reader"] is False, "reader crossed saved-only boundary")
rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
(ROOT / "PUBLIC_RECHECK_RESULT_20261008.json").write_text(rendered, encoding="utf-8")
print(rendered, end="")
