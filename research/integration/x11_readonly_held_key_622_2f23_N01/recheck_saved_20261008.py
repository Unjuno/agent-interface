#!/usr/bin/env python3
"""Verify the immutable #7231 packet and run its saved-data auditor in temp."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
MANIFEST_SHA256 = "ea297f47c05b34ae7c7187576dd4c9fef4d9f8d9387e91bf37780052b75b4b83"
AUDITOR_SHA256 = "cd15a048fcb2a82327a98fe69c4cb794be671d5e0a0ecc2146e2c70b7d9b993a"
sha256 = lambda data: hashlib.sha256(data).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


manifest_bytes = (ROOT / "MANIFEST.json").read_bytes()
require(sha256(manifest_bytes) == MANIFEST_SHA256, "pinned manifest identity mismatch")
manifest = json.loads(manifest_bytes)
require(type(manifest) is list and len(manifest) == 95, "manifest shape/count mismatch")
listed: set[str] = set()
for item in manifest:
    name = item["path"]
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts, f"unsafe path: {name}")
    require(name not in listed, f"duplicate path: {name}")
    listed.add(name)
    data = ROOT.joinpath(*path.parts).read_bytes()
    require(len(data) == item["bytes"] and sha256(data) == item["sha256"], f"manifest mismatch: {name}")

expected_unlisted = {
    "MANIFEST.json", "README.md", "README.txt", ".gitattributes",
    "RECHECK_20261008.md", "recheck_saved_20261008.py",
}
actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
required = listed | expected_unlisted
require(actual in (required, required | {"RECHECK_RESULT_20261008.json"}), "unexpected or missing packet file")
auditor = (ROOT / "independent-auditor.py.txt").read_bytes()
require(sha256(auditor) == AUDITOR_SHA256, "auditor identity mismatch")
freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
require(len(freeze["sources"]) == 82, "source-image count mismatch")
require(freeze["producer_sha256"] == "087898577083ab89cd796f037b41df3d12cbe7f95b04a630bbe3aa0a14819aa7", "producer identity mismatch")

with tempfile.TemporaryDirectory(prefix="held-key-622-saved-recheck-") as temp:
    tmp = Path(temp)
    work = tmp / "work/x11-key-observation-N01"
    (work / "result").mkdir(parents=True)
    (work / "source").mkdir()
    (work / "FREEZE.json").write_bytes((ROOT / "FREEZE.json").read_bytes())
    (work / "result/receipt.json").write_bytes((ROOT / "result/receipt.json").read_bytes())
    (work / "producer.py").write_bytes((ROOT / "producer.py.txt").read_bytes())
    for source in freeze["sources"]:
        relative = PurePosixPath(source["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe source path")
        saved = ROOT.joinpath("source", *relative.parts).with_name(relative.name + ".txt")
        data = saved.read_bytes()
        require(len(data) == source["bytes"] and sha256(data) == source["sha256"], f"frozen source mismatch: {source['path']}")
        destination = work.joinpath("source", *relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    completed = subprocess.run(
        [sys.executable, "-c", auditor.decode("utf-8")],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    require(completed.returncode == 0, f"saved auditor failed: {completed.stderr[-2000:]}")
    result = json.loads(completed.stdout.strip().splitlines()[-1])

require(result["result"] == "PASS_SCOPED_NATIVE_DATA_AUDIT", "unexpected audit disposition")
require(result["source_images"] == 82 and result["native_replayed"] is False, "audit scope mismatch")
require([x["name"] for x in result["controls"]] == ["physical_clear_hidden", "tracking_lost", "rescue_hidden"], "mutation controls differ")
require(all(x["refused"] for x in result["controls"]), "a corruption control was accepted")
rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
(ROOT / "RECHECK_RESULT_20261008.json").write_text(rendered, encoding="utf-8")
print(rendered, end="")
