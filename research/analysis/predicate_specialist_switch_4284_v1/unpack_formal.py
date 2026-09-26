import base64,hashlib,zlib
from pathlib import Path
p=Path(__file__).resolve().parent
out=zlib.decompress(base64.b64decode((p/"FORMAL_RESULT.json.zlib.b64").read_text()))
expected="dbf74500b348c9a3503e0dd489bb04d9d00f5d6a47a0c9163d4cc615ea90bb31"
assert hashlib.sha256(out).hexdigest()==expected
Path("FORMAL_RESULT.restored.json").write_bytes(out)
print(expected)
