"""Write a deterministic SHA-256 inventory for the retained A01 package."""
from __future__ import annotations

import hashlib
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
MANIFEST = PACKAGE / "SHA256SUMS"


def members():
    return sorted(path for path in PACKAGE.rglob("*") if path.is_file()
                   and path != MANIFEST and "__pycache__" not in path.parts)


def main():
    lines = []
    for path in members():
        relative = path.relative_to(PACKAGE).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {relative}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS_INVENTORY_WRITTEN members={len(lines)}")


if __name__ == "__main__":
    main()
