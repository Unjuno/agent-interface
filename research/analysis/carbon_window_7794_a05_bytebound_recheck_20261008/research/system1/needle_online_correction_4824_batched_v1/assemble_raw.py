"""Reconstruct and verify the exact raw construction JSON from base64 parts."""
import base64
import gzip
import hashlib
import sys
from pathlib import Path

EXPECTED_SHA256 = "9feb483c29c71191d519eb1be3842de44ead6e4df6c751defabd5fa40795af97"
EXPECTED_BYTES = 2_299_063


def main(directory: str, output: str) -> None:
    root = Path(directory)
    parts = sorted(root.glob("raw.json.gz.b64.part*"))
    if not parts:
        raise SystemExit("STOP_NO_RAW_PARTS")
    encoded = "".join(p.read_text(encoding="ascii") for p in parts)
    payload = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise SystemExit(f"STOP_RAW_HASH bytes={len(payload)} sha256={digest}")
    Path(output).write_bytes(payload)
    print(f"RAW_RECONSTRUCTED parts={len(parts)} bytes={len(payload)} sha256={digest}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

