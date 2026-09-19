#!/usr/bin/env python3
import base64, hashlib, lzma, sys
from pathlib import Path
EXPECTED='0115b1d9f0d607114782558f84e56d408b65743fd3f0af5a2677a7d3fb620aa7'
src=Path(__file__).with_name('formal-traces.jsonl.xz.b64')
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('formal-traces.jsonl')
if out.exists(): raise SystemExit('refuse existing output')
raw=lzma.decompress(base64.b64decode(src.read_text().strip()))
got=hashlib.sha256(raw).hexdigest()
if got!=EXPECTED: raise SystemExit(f'hash mismatch: {got}')
out.write_bytes(raw)
print(f'PASS {got} {len(raw)}')
