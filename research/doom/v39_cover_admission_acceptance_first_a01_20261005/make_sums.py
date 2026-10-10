"""Regenerate the additive package's SHA-256 manifest, excluding itself."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).parent
rows = [
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
    for path in sorted(ROOT.rglob("*"))
    if path.is_file() and path.name != "SHA256SUMS" and "__pycache__" not in path.parts
]
(ROOT / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} SHA-256 entries")
