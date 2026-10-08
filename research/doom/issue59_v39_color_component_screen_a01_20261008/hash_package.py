from hashlib import sha256
from pathlib import Path

root = Path(__file__).resolve().parent
lines = []
for path in sorted(root.iterdir()):
    if path.is_file() and path.name != "SHA256SUMS.txt":
        lines.append(f"{sha256(path.read_bytes()).hexdigest()}  {path.name}")
(root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
print(f"wrote checksums for {len(lines)} package files")

