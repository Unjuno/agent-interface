from pathlib import Path
import base64, lzma, tarfile, io, sys
base=Path(sys.argv[1])
parts=sorted(base.parent.glob(base.name+".part*"))
if not parts: raise SystemExit("no bundle parts")
b64="".join(p.read_text().strip() for p in parts)
data=base64.b64decode(b64, validate=True)
root=Path(sys.argv[2]); root.mkdir(parents=True, exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(data)), mode="r:") as tf:
    for m in tf.getmembers():
        if not m.isfile() or "/" in m.name or m.name.startswith("."):
            raise SystemExit("unsafe bundle member")
    tf.extractall(root, filter="data")
print(len(data))
