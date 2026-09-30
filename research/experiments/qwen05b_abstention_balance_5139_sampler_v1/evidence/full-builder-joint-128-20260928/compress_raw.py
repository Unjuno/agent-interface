import base64, gzip, hashlib
from pathlib import Path
raw=Path(__file__).with_name("construction_sentinel_1.json")
packed=gzip.compress(raw.read_bytes(),mtime=0)
gz=raw.with_suffix(".json.gz")
gz.write_bytes(packed)
b64=raw.with_suffix(".json.gz.base64")
b64.write_text(base64.b64encode(packed).decode("ascii")+"\n",encoding="ascii")
print(f"raw_sha256={hashlib.sha256(raw.read_bytes()).hexdigest()} raw_bytes={raw.stat().st_size}")
print(f"gzip_sha256={hashlib.sha256(packed).hexdigest()} gzip_bytes={len(packed)}")
print(f"base64_sha256={hashlib.sha256(b64.read_bytes()).hexdigest()} base64_bytes={b64.stat().st_size}")

