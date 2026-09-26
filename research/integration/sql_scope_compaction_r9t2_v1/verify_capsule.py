#!/usr/bin/env python3
import base64, hashlib, io, json, pathlib, tarfile, sys

ROOT = pathlib.Path(__file__).resolve().parent
cap = json.loads((ROOT / "CAPSULE.json").read_text())
chunks = []
for part in cap["parts"]:
    data = (ROOT / part["path"]).read_bytes()
    if len(data) != part["chars"]:
        raise SystemExit(f"part length mismatch: {part['path']}")
    if hashlib.sha256(data).hexdigest() != part["sha256"]:
        raise SystemExit(f"part sha256 mismatch: {part['path']}")
    chunks.append(data)
encoded = b"".join(chunks)
archive = base64.b64decode(encoded, validate=True)
if len(archive) != cap["archive_bytes"]:
    raise SystemExit("archive size mismatch")
if hashlib.sha256(archive).hexdigest() != cap["archive_sha256"]:
    raise SystemExit("archive sha256 mismatch")

dst = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "r9t2-restored")
if dst.exists():
    raise SystemExit("destination exists")
dst.mkdir(parents=True)
root = dst.resolve()
with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as tf:
    members = tf.getmembers()
    files = [m for m in members if m.isfile()]
    if len(files) != cap["file_count"]:
        raise SystemExit("file count mismatch")
    if sum(m.size for m in files) != cap["expanded_bytes"]:
        raise SystemExit("expanded size mismatch")
    for m in members:
        if m.issym() or m.islnk():
            raise SystemExit("links not allowed")
        target = (dst / m.name).resolve()
        if target != root and root not in target.parents:
            raise SystemExit("unsafe member")
    tf.extractall(dst)
print(json.dumps({"status":"PASS","archive_sha256":cap["archive_sha256"],"files":cap["file_count"]}, sort_keys=True))
