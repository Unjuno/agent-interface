from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "FILES.sha256.json"


def audit() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema"] == "producer-scorer-occurrence-files-v1"
    checked = []
    for row in manifest["files"]:
        path = ROOT / row["path"]
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        assert len(data) == row["bytes"], f"size mismatch: {row['path']}"
        assert actual == row["sha256"], f"hash mismatch: {row['path']}"
        checked.append(row["path"])
    return {
        "schema": "producer-scorer-occurrence-manifest-audit-v1",
        "status": "PASS",
        "checked_files": len(checked),
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "excluded_self_references": ["FILES.sha256.json", "MANIFEST_AUDIT.json"],
    }


if __name__ == "__main__":
    result = audit()
    target = ROOT / "MANIFEST_AUDIT.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
