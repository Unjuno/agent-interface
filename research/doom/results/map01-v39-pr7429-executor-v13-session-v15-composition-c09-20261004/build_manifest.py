import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
derived = {"MANIFEST.json", "AUDIT.json", "AUDIT.exit.txt"}
items = []
for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name not in derived):
    data = path.read_bytes()
    items.append({"path": path.relative_to(root).as_posix(),
                  "bytes": len(data),
                  "sha256": hashlib.sha256(data).hexdigest()})
(root / "MANIFEST.json").write_text(
    json.dumps({"schema": "sha256-manifest-v1", "files": items}, indent=2) + "\n",
    encoding="utf-8")
print(f"MANIFEST_FILES={len(items)}")
