from __future__ import annotations
import base64,gzip,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
src=ROOT/"RAW.json.gz.b64"
raw=gzip.decompress(base64.b64decode(src.read_text()))
expected="1758bf82f0a9894de23cd307ca15e75c53269b30db5cdb1c3340e7635374461f"
if hashlib.sha256(raw).hexdigest()!=expected: raise SystemExit("RAW_SHA256_MISMATCH")
out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/"RAW.restored.json"
out.write_bytes(raw)
print("PASS_RESTORE_RAW",out)
