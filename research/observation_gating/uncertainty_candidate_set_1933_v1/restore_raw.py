from __future__ import annotations
import base64,gzip,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parent
src=R/"formal-01"/"RAW.json.gz.b64"
out=Path(sys.argv[1]) if len(sys.argv)>1 else R/"formal-01"/"RAW.restored.json"
raw=gzip.decompress(base64.b64decode(src.read_bytes(), validate=True))
expected="681e55c107034609c0f85fa9a12bd9450af4725233a7db2e416b7142e438040d"
if hashlib.sha256(raw).hexdigest()!=expected: raise SystemExit("raw_sha256_mismatch")
out.write_bytes(raw)
print("PASS_RESTORE_RAW", len(raw), expected)
