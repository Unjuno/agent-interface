from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path("/app")
BASE = Path("/allocation")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    freeze_path = BASE / "FREEZE.json"
    manifest_path = BASE / "source_manifest.json"
    freeze = json.loads(freeze_path.read_bytes())
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert freeze["allocation_id"] == manifest["allocation_id"]
    assert freeze["main_sha"] == manifest["main_sha"] == os.environ["OBSTAC_SOURCE_COMMIT"]
    assert freeze["source_manifest_sha256"] == sha(manifest_path)
    assert freeze["container"]["image_id"] == os.environ["OBSTAC_IMAGE_ID"]
    checked = []
    for item in manifest["files"]:
        path = ROOT / item["path"]
        actual = sha(path)
        assert actual == item["sha256"], f"source hash mismatch: {item['path']}"
        checked.append({"path": item["path"], "sha256": actual})
    print(json.dumps({
        "audit": "PASS_PREFLIGHT_FREEZE_SOURCE_HASHES",
        "allocation_id": freeze["allocation_id"],
        "main_sha": freeze["main_sha"],
        "freeze_sha256": sha(freeze_path),
        "source_manifest_sha256": sha(manifest_path),
        "image_id": freeze["container"]["image_id"],
        "files_verified": len(checked),
        "files": checked,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
