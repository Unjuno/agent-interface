import base64,hashlib,zlib
from pathlib import Path
p=Path(__file__).resolve().parent
out=zlib.decompress(base64.b64decode((p/"FORMAL_RESULT.json.zlib.b64").read_text()))
expected="822fc3f64dc1edcd773ebcf92cbeac42f91eb1999fbd031fa74d02e41f2dbbeb"
assert hashlib.sha256(out).hexdigest()==expected
Path("FORMAL_RESULT.restored.json").write_bytes(out)
print(expected)
