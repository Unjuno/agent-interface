from decimal import Decimal
import hashlib
import json
from pathlib import Path


def blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def main():
    assert blob(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
    assert Decimal("1.125") + Decimal("2.875") == Decimal("4.000")
    fixture = json.loads((Path(__file__).parent / "fixture.json").read_text())
    for src in fixture["sources"].values():
        assert blob(src["raw_text"].encode()) == src["git_blob_sha"], src["path"]
    print(f"PASS mechanics sources={len(fixture['sources'])}")

if __name__ == "__main__":
    main()
