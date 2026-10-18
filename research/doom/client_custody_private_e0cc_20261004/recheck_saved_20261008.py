#!/usr/bin/env python3
"""Verify #7275's inert public packet only; never execute archived code."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
MANIFEST_SHA256 = "cbe28cda8f9a7d5f9e09166ec9bcb8ef612fe987dd5a5098a901d93252c341ce"
sha256 = lambda data: hashlib.sha256(data).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


manifest_bytes = (ROOT / "MANIFEST.json").read_bytes()
require(sha256(manifest_bytes) == MANIFEST_SHA256, "pinned manifest identity mismatch")
manifest = json.loads(manifest_bytes)
require(manifest["scope"] == "inert original and stderr evidence; source scopes separate; retained first failures", "manifest scope changed")
members = manifest["members"]
require(type(members) is list and len(members) == 47, "manifest member count mismatch")
listed: set[str] = set()
total_bytes = 0
for entry in members:
    name = entry["path"]
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts, f"unsafe manifest path: {name}")
    require(name not in listed, f"duplicate manifest path: {name}")
    listed.add(name)
    data = ROOT.joinpath(*path.parts).read_bytes()
    require(len(data) == entry["bytes"] and sha256(data) == entry["sha256"], f"member mismatch: {name}")
    total_bytes += len(data)

expected_wrappers = {
    "MANIFEST.json", "RECHECK_20261008.md", "recheck_saved_20261008.py",
    "RECHECK_RESULT_20261008.json",
}
actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
required = listed | expected_wrappers
require(actual in (required, required - {"RECHECK_RESULT_20261008.json"}), "unexpected packet path")

shape = json.loads((ROOT / "shape_results.json").read_bytes())
peers = json.loads((ROOT / "owned_peer_results.json").read_bytes())
multi = json.loads((ROOT / "stderr-supplement/roundtrip-pressure/multi/RESULT.json").read_bytes())
parallel = json.loads((ROOT / "stderr-supplement/roundtrip-pressure/parallel/RESULT.json").read_bytes())
require(peers["candidate_sha256"] == "c513bf6c736a8bbaee296ebbc2551e163fd283b43245996612f949453157833f", "candidate identity changed")
require(multi["source_sha256"] == "3a784bc3d1d68876871ac9425adc245026c208e36041a12f0eddd84e1334d1a1", "stderr candidate identity changed")
for item in (multi, parallel):
    require(item["exact_requests_responses"] == 4 and item["drained_bytes"] == 1_228_800 and item["retained_tail_bytes"] == 65_536, "roundtrip summary changed")

result = {
    "status": "PASS_PACKET_INTEGRITY_ONLY",
    "manifest_sha256": MANIFEST_SHA256,
    "manifest_members": len(members),
    "manifest_bytes": total_bytes,
    "archived_shape_cases": len(shape.get("cases", [])) if isinstance(shape, dict) else None,
    "archived_owned_peer_cases": len(peers["cases"]),
    "roundtrip_cases_checked": 2,
    "candidate_or_peer_replayed": False,
    "formal_allocation_replayed": False,
    "source_owner_or_application_approval": False,
    "whole_goal_complete": False,
}
rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
(ROOT / "RECHECK_RESULT_20261008.json").write_text(rendered, encoding="utf-8")
print(rendered, end="")
