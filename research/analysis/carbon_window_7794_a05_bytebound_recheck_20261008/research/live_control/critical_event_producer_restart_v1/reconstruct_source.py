from pathlib import Path
import base64,hashlib,lzma,sys
root=Path(__file__).parent
s="".join("".join(p.read_text().split()) for p in sorted(root.glob("source.part*.b64")))
b=base64.b64decode(s,validate=True)
expected="0d2a5664d3a73aecc331ffd52e689fcf46f4113ebb15c0f476d20d0dcac8c304"
assert hashlib.sha256(b).hexdigest()==expected
out=root/"source_bundle.tar.xz"
out.write_bytes(b)
print(expected)
