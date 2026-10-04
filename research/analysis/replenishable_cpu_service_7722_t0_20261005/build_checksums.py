#!/usr/bin/env python3
"""Write sorted SHA256SUMS for all retained package files."""
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
rows = []
for path in sorted(root.rglob("*")):
    if not path.is_file() or path.name == "SHA256SUMS" or "__pycache__" in path.parts:
        continue
    rel = path.relative_to(root).as_posix()
    rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}")
(root / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} retained-file hashes")
