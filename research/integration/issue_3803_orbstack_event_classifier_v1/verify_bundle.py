"""Verify the additive #3803 bundle; refuse bytecode/cache contamination."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "SHA256SUMS"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory() -> dict[str, str]:
    files = {}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == MANIFEST:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if "__pycache__" in Path(relative).parts or relative.endswith(".pyc"):
            raise ValueError("cache artifact forbidden in evidence bundle: " + relative)
        files[relative] = digest(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    actual = inventory()
    if args.write:
        MANIFEST.write_text("".join(f"{value}  {name}\n" for name, value in sorted(actual.items())),
                            encoding="utf-8", newline="\n")
    expected = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        checksum, name = line.split("  ", 1)
        if name in expected:
            raise ValueError("duplicate manifest entry: " + name)
        expected[name] = checksum
    if expected != actual:
        raise ValueError(json.dumps({"missing": sorted(set(expected) - set(actual)),
                                     "unlisted": sorted(set(actual) - set(expected)),
                                     "mismatched": sorted(name for name in set(expected) & set(actual)
                                                          if expected[name] != actual[name])}, sort_keys=True))
    print(json.dumps({"status": "PASS_BUNDLE_SHA256", "files": len(actual)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
