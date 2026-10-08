# Formal T1 artifact

raw.json.gz.b64 contains the exact one-line JSON emitted by the frozen runner, gzip-compressed and base64-encoded in memory. The independent audit's raw SHA-256 is for the decompressed bytes.

On Python 3:
```python
import base64, gzip, pathlib
encoded = pathlib.Path("raw.json.gz.b64").read_bytes()
raw = gzip.decompress(base64.b64decode(encoded))
assert len(raw) == 198339
assert __import__("hashlib").sha256(raw).hexdigest() == "fa237492dd6657da2b98a3b48bc994851e057a70df1c252fbe974a2a5ea22f3a"
pathlib.Path("raw.json").write_bytes(raw)
```

The archive is a lossless transport encoding, not a transformed result. Do not overwrite the frozen raw or audit.
