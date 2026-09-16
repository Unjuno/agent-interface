#!/usr/bin/env python3
import base64, hashlib, lzma, sys
from pathlib import Path
EXPECTED='ab155b1d796c5d02900248735e9819c3ca71345f41df7d3431de44f167a8f86b'
src=Path(__file__).with_name('formal-traces.jsonl.xz.b64')
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('formal-traces.jsonl')
if out.exists(): raise SystemExit('refuse existing output')
raw=lzma.decompress(base64.b64decode(src.read_text().strip()))
got=hashlib.sha256(raw).hexdigest()
if got!=EXPECTED: raise SystemExit(f"hash mismatch: {got}")
out.write_bytes(raw)
print(f"PASS {got} {len(raw)}")
