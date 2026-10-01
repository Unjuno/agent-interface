#!/usr/bin/env python3
import base64,gzip,hashlib,sys
from pathlib import Path
EXPECTED='fc02c4cd635e1aabf629e312b98389ec45e345f9961174c18971e17524c180a4'
s=Path(__file__).with_name('formal-result.json.gz.b64')
o=Path(sys.argv[1]) if len(sys.argv)>1 else Path('reconstructed-formal-result.json')
if o.exists(): raise SystemExit('refuse existing output')
r=gzip.decompress(base64.b64decode(s.read_text().strip()))
h=hashlib.sha256(r).hexdigest()
if h!=EXPECTED: raise SystemExit(f'hash mismatch: {h}')
o.write_bytes(r)
print(f'PASS {h} {len(r)}')
