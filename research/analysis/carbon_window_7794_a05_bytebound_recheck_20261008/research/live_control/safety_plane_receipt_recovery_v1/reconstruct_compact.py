from pathlib import Path
import base64,hashlib
parts=sorted(Path('.').glob("compact.part*.b64"))
raw=base64.b64decode("".join("".join(p.read_text().split()) for p in parts))
sha=hashlib.sha256(raw).hexdigest()
assert sha=="8bb0a0424c109e2c0a450df69a3e52b1a1e0987401aa1a755cef3bbcae5c1525",(sha,"8bb0a0424c109e2c0a450df69a3e52b1a1e0987401aa1a755cef3bbcae5c1525")
Path("compact_evidence.tar.xz").write_bytes(raw)
print(sha,len(raw))
