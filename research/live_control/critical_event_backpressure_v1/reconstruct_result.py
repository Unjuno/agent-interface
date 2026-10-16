from pathlib import Path
import base64,hashlib,lzma,sys
root=Path(__file__).parent
s="".join("".join((root/f"result.part{i:02d}.b64").read_text().split()) for i in range(4))
b=base64.b64decode(s,validate=True)
expected="d409f0f9ca28897b389dc00f3d4d11c8556ab58483754c86f6e19936c05ad72c"
assert hashlib.sha256(b).hexdigest()==expected
out=root/"result_bundle.tar.xz"
out.write_bytes(b)
print(expected)
