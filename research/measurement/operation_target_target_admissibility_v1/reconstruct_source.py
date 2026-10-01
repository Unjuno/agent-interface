from pathlib import Path
import base64,hashlib,tarfile
raw=base64.b64decode(Path('source_bundle.b64').read_text())
expected='7bb485b1f2fcf907246de8473d767d3a308a707b35e37b226e44fcaab836eea1'
assert hashlib.sha256(raw).hexdigest()==expected
Path('source_bundle.readback.tar.gz').write_bytes(raw)
with tarfile.open('source_bundle.readback.tar.gz','r:gz') as t:t.extractall('readback')
print(expected)
