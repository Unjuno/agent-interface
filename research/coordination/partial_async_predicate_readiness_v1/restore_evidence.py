#!/usr/bin/env python3
import argparse, base64, hashlib, io, json, lzma, os, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("destination")
    args=ap.parse_args()
    dest=Path(args.destination)
    if dest.exists(): raise SystemExit("destination exists")
    pm=json.loads((ROOT/"PARTS_MANIFEST.json").read_text())
    em=json.loads((ROOT/"EVIDENCE_MANIFEST.json").read_text())
    chunks=[]
    for row in pm["ordered_parts"]:
        data=(ROOT/row["file"]).read_bytes()
        if len(data)!=row["bytes"] or sha(data)!=row["sha256"]:
            raise SystemExit(f"part mismatch: {row['file']}")
        chunks.append(data)
    b64=b"".join(chunks)
    if len(b64)!=pm["reconstructed_base64_bytes"] or sha(b64)!=pm["reconstructed_base64_sha256"]:
        raise SystemExit("base64 reconstruction mismatch")
    xz=base64.b64decode(b64, validate=True)
    if len(xz)!=em["decoded_xz_bytes"] or sha(xz)!=em["decoded_xz_sha256"]:
        raise SystemExit("decoded capsule mismatch")
    tar_bytes=lzma.decompress(xz)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
        members=tf.getmembers()
        if len(members)!=em["member_count"]:
            raise SystemExit("member count mismatch")
        expected=set(em["members"])
        actual={m.name for m in members}
        if actual!=expected:
            raise SystemExit("member set mismatch")
        for m in members:
            p=Path(m.name)
            if p.is_absolute() or ".." in p.parts or not m.isfile():
                raise SystemExit(f"unsafe member: {m.name}")
        dest.mkdir()
        for m in members:
            out=dest/m.name
            out.parent.mkdir(parents=True, exist_ok=True)
            f=tf.extractfile(m)
            if f is None: raise SystemExit(f"missing member bytes: {m.name}")
            out.write_bytes(f.read())
    print(json.dumps({"status":"PASS","members":len(em["members"]),"destination":str(dest)}, sort_keys=True))
if __name__=="__main__":
    main()
