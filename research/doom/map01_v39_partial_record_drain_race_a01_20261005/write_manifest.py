import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
manifest = ROOT / "research" / "doom" / "map01_v39_partial_record_drain_race_a01_20261005" / "SHA256SUMS"
lines = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or "__pycache__" in path.parts or path == manifest:
        continue
    digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    lines.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {len(lines)} checksums")
