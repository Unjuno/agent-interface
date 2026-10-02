"""Reassemble the size-capped GitHub base64 parts and verify exact adapter bytes."""
import argparse
import base64
import hashlib
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", required=True, help="directory containing adapter_model.safetensors.part-*.b64")
    ap.add_argument("--out", required=True)
    ap.add_argument("--expected-sha256", default="c51dcfff55254b43559a8d02a831707fe309080d5fd958a44bef2d431f2f0f84")
    ap.add_argument("--expected-bytes", type=int, default=2175168)
    args = ap.parse_args()
    root = Path(args.parts)
    paths = sorted(root.glob("adapter_model.safetensors.part-*.b64"))
    if len(paths) != 6:
        raise SystemExit(f"expected 6 ordered base64 parts; found {len(paths)}")
    chunks = []
    for path in paths:
        encoded = path.read_bytes()
        if encoded.startswith(b"\xef\xbb\xbf"):
            encoded = encoded[3:]
        chunks.append(base64.b64decode(encoded, validate=True))
    payload = b"".join(chunks)
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != args.expected_bytes or digest != args.expected_sha256:
        raise SystemExit(json.dumps({"state": "STOP_PART_REASSEMBLY_MISMATCH", "bytes": len(payload), "sha256": digest}))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    print(json.dumps({"state": "PASS_EXACT_REASSEMBLY", "parts": len(paths), "bytes": len(payload), "sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
