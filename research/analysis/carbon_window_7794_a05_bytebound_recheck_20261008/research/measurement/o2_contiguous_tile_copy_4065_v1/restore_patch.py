#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, sys

HERE = Path(__file__).resolve().parent
PARTS = [
    ("allocation.patch.part00", "a6a2449f305bc958cdc6558072e8d9ef7d2c0843626420742967f8cbced52254"),
    ("allocation.patch.part01", "25736292de813e953486d7fa204d89962a7de0ce52756061d7dfea00cfb00d02"),
    ("allocation.patch.part02", "c8429b599393ab0a37721aecb6c12359281eaacc46b880e791d55ff400b1a8ba"),
    ("allocation.patch.part03", "01b60128f434727bae331df7cf3852ab69a9898ef1fea1bde886208b64346936"),
]
FULL = "513ca7552d4240474020c337f53bfdf846751d9f4c5ed65dc7c11fbbe3b4b5ca"
SIZE = 1327767

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: restore_patch.py FRESH_PATCH_PATH")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("output already exists")
    chunks = []
    for name, expected in PARTS:
        data = (HERE / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit("part hash mismatch: " + name)
        chunks.append(data)
    raw = b"".join(chunks)
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != FULL:
        raise SystemExit("full patch mismatch")
    out.write_bytes(raw)
    print(json.dumps({"status":"PASS_PATCH_RESTORE","bytes":len(raw),"sha256":FULL},sort_keys=True))

if __name__ == "__main__":
    main()
