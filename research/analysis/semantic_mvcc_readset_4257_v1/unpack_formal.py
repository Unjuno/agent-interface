import base64,hashlib,zlib
from pathlib import Path
p=Path(__file__).resolve().parent
out=zlib.decompress(base64.b64decode((p/"FORMAL_RESULT.json.zlib.b64").read_text()))
expected="d17e4cfd32cdb90ed796f936a0e2b3e143f584d5cf18170c7ad35324fdef3831"
assert hashlib.sha256(out).hexdigest()==expected
Path("FORMAL_RESULT.restored.json").write_bytes(out)
print(expected)
