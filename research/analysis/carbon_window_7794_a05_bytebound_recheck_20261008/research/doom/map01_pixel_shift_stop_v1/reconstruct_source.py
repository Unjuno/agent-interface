from pathlib import Path
import base64,hashlib
root=Path(__file__).parent
s="".join("".join(p.read_text().split()) for p in sorted(root.glob("source.part*.b64")))
b=base64.b64decode(s,validate=True)
expected="b4c9650f7dbee660653191ef5b23c83f34f79e0c441b6c08dc0d90c230a21b61"
assert hashlib.sha256(b).hexdigest()==expected
out=root/"source_bundle.tar.xz"
out.write_bytes(b)
print(expected)
