#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json

def sha(b):
    return hashlib.sha256(b).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ns = ap.parse_args()
    here = Path(__file__).resolve().parent
    out = Path(ns.out)
    if out.exists():
        raise SystemExit("REFUSE_EXISTING_OUTPUT")
    pack = json.loads((here / "PACK.json").read_text())
    blocks = []
    for ent in pack["parts"]:
        b = (here / ent["name"]).read_bytes()
        if len(b) != ent["bytes"] or sha(b) != ent["sha256"]:
            raise SystemExit("PART_MISMATCH")
        blocks.append(b)
    data = b"".join(blocks)
    if len(data) != pack["original_patch_bytes"] or sha(data) != pack["original_patch_sha256"]:
        raise SystemExit("PATCH_MISMATCH")
    out.write_bytes(data)
    print(json.dumps({"status": "PASS_PATCH_RECONSTRUCTION", "bytes": len(data), "sha256": sha(data)}, sort_keys=True))

if __name__ == "__main__":
    main()
