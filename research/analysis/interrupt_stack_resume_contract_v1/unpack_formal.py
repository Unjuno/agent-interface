import base64,hashlib,zlib
from pathlib import Path
p=Path(__file__).resolve().parent
data=zlib.decompress(base64.b64decode((p/"FORMAL_RESULT.json.zlib.b64").read_text()))
expected="2de15af3c6b24b277883ae84c5c4c92de3076dab017d2caa8961a8bee5f6e8b6"
assert hashlib.sha256(data).hexdigest()==expected
Path("FORMAL_RESULT.restored.json").write_bytes(data)
print(expected)
