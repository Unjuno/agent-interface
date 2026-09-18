#!/usr/bin/env python3
import base64,gzip,hashlib,io,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
raw=gzip.decompress(base64.b64decode((HERE/'SOURCE_BUNDLE.tar.gz.b64').read_text().strip()))
expected='cd7a93f933b38d360adcbffaddf0671b9f64dbfc8d986b4a7fdc5fedaa3771ca'
if hashlib.sha256(gzip.compress(raw,mtime=0)).hexdigest()==expected:
    pass
# archive hash is checked on decoded gzip bytes below
gz=base64.b64decode((HERE/'SOURCE_BUNDLE.tar.gz.b64').read_text().strip())
if hashlib.sha256(gz).hexdigest()!=expected: raise SystemExit('bundle hash mismatch')
with tarfile.open(fileobj=io.BytesIO(gzip.decompress(gz)),mode='r:') as t:
    t.extractall(HERE/'SOURCE_RECONSTRUCTED',filter='data')
print(expected)
