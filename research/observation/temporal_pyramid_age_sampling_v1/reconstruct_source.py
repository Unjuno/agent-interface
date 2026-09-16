from pathlib import Path
import base64,hashlib
r=Path(__file__).parent
s="".join("".join(p.read_text().split()) for p in sorted(r.glob("source.part*.b64")))
b=base64.b64decode(s,validate=True)
expected="ad48f224d68d55e9e108783da8da96ce99275810dfe64457f10d4a7db1ee8ebc"
assert hashlib.sha256(b).hexdigest()==expected
(r/"source_bundle.tar.xz").write_bytes(b)
print(expected)
