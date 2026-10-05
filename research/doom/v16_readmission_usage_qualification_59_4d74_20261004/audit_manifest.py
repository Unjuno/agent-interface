"""Verify the additive package's byte inventory."""
import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent


def main():
    manifest = json.loads((PACKAGE / "FILES.sha256.json").read_text(encoding="utf-8"))
    members = manifest["members"]
    for relative, expected in members.items():
        path = (PACKAGE / relative).resolve()
        assert PACKAGE.resolve() in path.parents, relative
        raw = path.read_bytes()
        assert len(raw) == expected["bytes"], relative
        assert hashlib.sha256(raw).hexdigest() == expected["sha256"], relative
    print(json.dumps({"status": "PASS", "members": len(members)}, sort_keys=True))


if __name__ == "__main__":
    main()
