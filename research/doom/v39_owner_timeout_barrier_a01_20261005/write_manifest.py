"""Write package SHA-256 inventory, excluding interpreter caches."""
import hashlib
from pathlib import Path

PKG = Path(__file__).resolve().parent
files = sorted(
    path for path in PKG.rglob("*")
    if path.is_file() and "__pycache__" not in path.parts and path.name != "SHA256SUMS.txt"
)
lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(PKG).as_posix()}" for path in files]
(PKG / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"manifest entries: {len(lines)}")
