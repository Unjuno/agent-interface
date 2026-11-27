"""Write a deterministic SHA-256 inventory for the final P09 packet."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "SHA256SUMS-PACKET"
rows = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path == TARGET or "__pycache__" in path.parts or path.suffix == ".pyc":
        continue
    rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}")
TARGET.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
print(f"{len(rows)} files hashed")
