#!/usr/bin/env python3
"""Reconstruct exact #503 GitHub Actions evidence archives from retained Base64 chunks."""
from __future__ import annotations
import base64, hashlib, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPECS = {
    "full": {
        "parts": [f"full_artifact.part{i:02d}.b64" for i in range(4)],
        "zip_sha256": "74f38f7a9e9c567fa9a41f5ded5c169cbc1e3ca7960da467e41bd79b5e408cbd",
        "members": {
            "result.json": "931f93977a6e3cf32d0529af6113b135660defb46f38c9c3185d3638a0b9369e",
            "audit_result.json": "56503b6b544477d4b65bb8d9fabc5b8fce87ed94256c509aeec9de803607f7be",
            "negative_tests.jsonl": "88a7239b8ee0188c5f1e63c880ca0289f965d767bde297e36237a8212e9c9bbf",
        },
    },
    "construction": {
        "parts": [f"construction_artifact.part{i:02d}.b64" for i in range(3)],
        "zip_sha256": "4c6edaeb3a3d3084db9f4aec31423249f9c6d42d62acbe11c5ba11326962147b",
        "members": {},
    },
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def reconstruct(kind: str, outdir: Path) -> Path:
    spec = SPECS[kind]
    text = "".join((ROOT / name).read_text() for name in spec["parts"])
    raw = base64.b64decode("".join(text.split()), validate=True)
    got = digest(raw)
    if got != spec["zip_sha256"]:
        raise SystemExit(f"{kind} ZIP SHA mismatch: {got}")
    outdir.mkdir(parents=True, exist_ok=True)
    zpath = outdir / f"map01-first-useful-feedback-{kind}-503.zip"
    zpath.write_bytes(raw)
    with zipfile.ZipFile(zpath) as zf:
        zf.extractall(outdir / kind)
        names = set(zf.namelist())
        for name, want in spec["members"].items():
            if name not in names:
                raise SystemExit(f"missing {kind} member {name}")
            member = zf.read(name)
            if digest(member) != want:
                raise SystemExit(f"{kind} member SHA mismatch: {name}")
    print(f"{kind}: {got} PASS")
    return zpath

def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "decoded"
    for kind in ("construction", "full"):
        reconstruct(kind, out)
if __name__ == "__main__":
    main()
