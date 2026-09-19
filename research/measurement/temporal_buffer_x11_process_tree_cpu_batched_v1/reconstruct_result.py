from pathlib import Path
import base64,gzip,hashlib,sys
s=Path('FORMAL_RESULT.json.gz.b64').read_text()
raw=gzip.decompress(base64.b64decode(s))
expected='8c4cf01025a9ba8baca18e65159e500305ba2fce4bfca670fcd79a376c6cd0b3'
assert hashlib.sha256(raw).hexdigest()==expected
out=Path(sys.argv[1] if len(sys.argv)>1 else 'FORMAL_RESULT.reconstructed.json')
out.write_bytes(raw)
print(expected)
