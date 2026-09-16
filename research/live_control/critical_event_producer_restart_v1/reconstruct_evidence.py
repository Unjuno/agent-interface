from pathlib import Path
import base64,hashlib
root=Path(__file__).parent
s="".join("".join(p.read_text().split()) for p in sorted(root.glob("evidence.part*.b64")))
b=base64.b64decode(s,validate=True)
expected="c568885c914196496624129b98d9fa981f80c3a664abc5e17c035a6188ac9bd3"
assert hashlib.sha256(b).hexdigest()==expected
(root/"evidence.tar.xz").write_bytes(b)
print(expected)
