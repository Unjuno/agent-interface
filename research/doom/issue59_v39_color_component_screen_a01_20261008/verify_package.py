import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
entries = {}
for line in (root / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
    digest, name = line.split("  ", 1)
    entries[name] = digest
files = {path.name for path in root.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"}
assert set(entries) == files
assert all(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
           for name, digest in entries.items())
for name in ("exit.txt", "optimized-exit.txt", "AUDIT.exit.txt"):
    assert (root / name).read_text(encoding="ascii").strip() == "0"
assert (root / "normal-output.sha256").read_text().strip() == (
    root / "optimized-output.sha256").read_text().strip()
print(f"PASS: {len(entries)} files hashed; normal/optimized output and retained exits match")

