import base64, gzip, hashlib
from pathlib import Path

raw = Path("dataset.json").read_bytes()
compressed = gzip.compress(raw, compresslevel=9, mtime=0)
encoded = base64.b64encode(compressed) + b"\n"
Path("dataset.json.gz.b64").write_bytes(encoded)
Path("dataset.json.gz").write_bytes(compressed)
restored = gzip.decompress(base64.b64decode(encoded))
assert restored == raw
assert hashlib.sha256(restored).hexdigest() == "d96c4072db2ee3bb1af7503a8ae98e062794072385a15099f32121a7a8caad4b"
print({
 "raw_bytes":len(raw),"raw_sha256":hashlib.sha256(raw).hexdigest(),
 "gzip_bytes":len(compressed),"gzip_sha256":hashlib.sha256(compressed).hexdigest(),
 "base64_bytes":len(encoded),"base64_sha256":hashlib.sha256(encoded).hexdigest(),
 "restore_byte_identity":restored==raw
})

