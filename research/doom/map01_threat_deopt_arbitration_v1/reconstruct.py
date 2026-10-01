#!/usr/bin/env python3
import base64,gzip,hashlib,sys
from pathlib import Path
EXPECTED_RAW_SHA256='64d8afb0d3175d54846f9f8988498910ca4d73d19e47a83ebbab61b43a37beae'
src=Path(__file__).with_name('formal-result.json.gz.b64')
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('reconstructed-formal-result.json')
if out.exists(): raise SystemExit('refuse existing output')
raw=gzip.decompress(base64.b64decode(src.read_text().strip()))
actual=hashlib.sha256(raw).hexdigest()
if actual!=EXPECTED_RAW_SHA256: raise SystemExit(f'hash mismatch: {actual}')
out.write_bytes(raw)
print(f'PASS {actual} {len(raw)}')
