#!/usr/bin/env python3
import hashlib, json, pathlib, tarfile, sys
ROOT=pathlib.Path(__file__).resolve().parent
cap=json.loads((ROOT/"CAPSULE.json").read_text())
arc=ROOT/cap["archive"]
data=arc.read_bytes()
if hashlib.sha256(data).hexdigest()!=cap["sha256"]: raise SystemExit("archive sha256 mismatch")
if len(data)!=cap["bytes"]: raise SystemExit("archive size mismatch")
dst=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "r9t2-restored")
if dst.exists(): raise SystemExit("destination exists")
dst.mkdir(parents=True)
with tarfile.open(arc,"r:xz") as tf:
    files=[m for m in tf.getmembers() if m.isfile()]
    if len(files)!=cap["file_count"]: raise SystemExit("file count mismatch")
    if sum(m.size for m in files)!=cap["expanded_bytes"]: raise SystemExit("expanded size mismatch")
    root=dst.resolve()
    for m in tf.getmembers():
        target=(dst/m.name).resolve()
        if not str(target).startswith(str(root)+"/"): raise SystemExit("unsafe member")
    tf.extractall(dst)
print(json.dumps({"status":"PASS","archive_sha256":cap["sha256"],"files":cap["file_count"]},sort_keys=True))
