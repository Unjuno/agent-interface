#!/usr/bin/env python3
import base64, hashlib, json, lzma, os, sys, tarfile, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
META=json.loads((ROOT/"EVIDENCE_BASE64.json").read_text())
if len(sys.argv)!=2:
    raise SystemExit("usage: restore_b64.py ABSENT_DEST")
dest=Path(sys.argv[1])
if dest.exists():
    raise SystemExit("destination exists")
encoded=b""
for p in META["parts"]:
    raw=(ROOT/p["path"]).read_bytes()
    if len(raw)!=p["chars"] or hashlib.sha256(raw).hexdigest()!=p["sha256"]:
        raise SystemExit("part mismatch: "+p["path"])
    encoded+=raw
archive=base64.b64decode(encoded, validate=True)
if len(archive)!=META["archive_bytes"] or hashlib.sha256(archive).hexdigest()!=META["archive_sha256"]:
    raise SystemExit("archive mismatch")
tar_bytes=lzma.decompress(archive)
with tempfile.NamedTemporaryFile(delete=False) as f:
    f.write(tar_bytes); tmp=f.name
try:
    with tarfile.open(tmp,"r:") as tf:
        members=tf.getmembers()
        if len(members)!=META["expanded_files"]:
            raise SystemExit("member count mismatch")
        for m in members:
            pp=Path(m.name)
            if pp.is_absolute() or ".." in pp.parts or not m.isfile():
                raise SystemExit("unsafe member: "+m.name)
        dest.mkdir(parents=True)
        tf.extractall(dest, filter="data")
finally:
    os.unlink(tmp)
print(json.dumps({"status":"PASS_RESTORE","files":META["expanded_files"],"archive_sha256":META["archive_sha256"]},sort_keys=True))
