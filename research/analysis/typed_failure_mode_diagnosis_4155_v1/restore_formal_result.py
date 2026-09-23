from pathlib import Path
import base64, hashlib, lzma
p=Path(__file__).resolve().parent
encoded=(p/'FORMAL_RESULT.json.xz.b64').read_text().strip()
xz=base64.b64decode(encoded,validate=True)
assert hashlib.sha256(xz).hexdigest()=='3ea5287dc1fe1d42ba28e4bcd4d494023239f30d6e43ba84e020389ccfca681a'
raw=lzma.decompress(xz)
assert hashlib.sha256(raw).hexdigest()=='ca448279282edeb605114b7e641dca4564fcc2291db2131e964cfee86f65b8e8'
(p/'FORMAL_RESULT.restored.json').write_bytes(raw)
print(len(raw))
