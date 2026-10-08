"""Write the review-package SHA-256 manifest after retaining command output."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and
                   path.name != "SHA256SUMS" and "__pycache__" not in path.parts)
    rows = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
    manifest = ROOT / "SHA256SUMS"
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} review-package hashes")


if __name__ == "__main__":
    main()
