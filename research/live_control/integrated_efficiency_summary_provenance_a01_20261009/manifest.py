#!/usr/bin/env python3
"""Hash the completed A01 evidence package, excluding the manifest itself."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    files = []
    for path in sorted(HERE.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json" and "__pycache__" not in path.parts:
            raw = path.read_bytes()
            files.append({"path": path.relative_to(HERE).as_posix(), "bytes": len(raw),
                          "sha256": hashlib.sha256(raw).hexdigest()})
    output = {"schema": "integrated_efficiency_summary_provenance_a01_manifest_v1",
              "file_count": len(files), "files": files}
    (HERE / "MANIFEST.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": "WRITTEN", "file_count": len(files)}, indent=2))


if __name__ == "__main__":
    main()
