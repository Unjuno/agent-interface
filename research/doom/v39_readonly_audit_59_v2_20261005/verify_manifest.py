"""Check the final additive package's byte inventory."""
import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent


def main():
    manifest_path = PACKAGE / "FILES.sha256.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["members"]
    actual = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*") if path.is_file() and
        "__pycache__" not in path.parts
    } - {"FILES.sha256.json"}
    if actual != set(expected):
        raise SystemExit(json.dumps({
            "status": "FAIL", "missing": sorted(set(expected) - actual),
            "unlisted": sorted(actual - set(expected))}, sort_keys=True))
    for relative, values in expected.items():
        raw = (PACKAGE / relative).read_bytes()
        if len(raw) != values["bytes"] or hashlib.sha256(raw).hexdigest() != values["sha256"]:
            raise SystemExit(f"FAIL {relative}")
    print(json.dumps({"status": "PASS", "members": len(expected)}, sort_keys=True))


if __name__ == "__main__":
    main()
