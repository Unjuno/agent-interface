from __future__ import annotations
import base64,hashlib,lzma,sys
from pathlib import Path
RAW_SHA="c031f2cfc1283ce262cff53f237b00356e45f24eeeed4fb40b795bce1e3a444f"
XZ_SHA="7b12c28ee11a949dc62b5c809ee8b2e17b6da9bf3ed639eb85ef7252ca3bfd24"
data=base64.b64decode(Path(sys.argv[1]).read_text().strip(),validate=True)
if hashlib.sha256(data).hexdigest()!=XZ_SHA: raise SystemExit("xz hash mismatch")
raw=lzma.decompress(data)
if hashlib.sha256(raw).hexdigest()!=RAW_SHA: raise SystemExit("raw hash mismatch")
Path(sys.argv[2]).write_bytes(raw)
print("RESTORED",len(raw),RAW_SHA)
