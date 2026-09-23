"""Hash every retained evidence file except the manifest itself."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).parent / "evidence"
rows = []
for path in sorted(root.rglob("*")):
    if path.is_file() and path.name != "manifest.json":
        payload = path.read_bytes()
        rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(payload),
                     "sha256": hashlib.sha256(payload).hexdigest()})
out = {"schema": "agent-interface/issue-3587-evidence-manifest-v1", "files": rows}
(root / "manifest.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps({"files": len(rows), "bytes": sum(r["bytes"] for r in rows),
                  "sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()}))
