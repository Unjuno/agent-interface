import base64,hashlib,zlib
from pathlib import Path
p=Path(__file__).resolve().parent
out=zlib.decompress(base64.b64decode((p/"FORMAL_RESULT.json.zlib.b64").read_text()))
expected="d0a14107c0f64929ebff012a57191467c35f32af2d83af3e45715b6d2797fa0e"
assert hashlib.sha256(out).hexdigest()==expected
Path("FORMAL_RESULT.restored.json").write_bytes(out)
print(expected)
