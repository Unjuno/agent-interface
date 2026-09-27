import base64,hashlib,zlib
from pathlib import Path
p=Path(__file__).resolve().parent
out=zlib.decompress(base64.b64decode((p/"FORMAL_RESULT.json.zlib.b64").read_text()))
expected="b0a0ad24031ab50e0f410c78de6b4525edeae91ada87c787154bb8232024f117"
assert hashlib.sha256(out).hexdigest()==expected
Path("FORMAL_RESULT.restored.json").write_bytes(out)
print(expected)
