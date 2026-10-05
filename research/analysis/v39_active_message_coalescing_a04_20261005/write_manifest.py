"""Write a deterministic SHA-256 manifest for all retained A04 package files."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "SHA256SUMS"


def main() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
    MANIFEST.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
