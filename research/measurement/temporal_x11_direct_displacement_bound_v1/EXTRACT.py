from pathlib import Path
import base64,gzip,hashlib,io,tarfile
HERE=Path(__file__).resolve().parent
EXPECTED='1a320526d3c842f9298019c8cd551188583b59777461bf47deb86f81fa3ec1de'
b64=b''.join((HERE/f'SOURCE_BUNDLE.b64.part{i:02d}').read_bytes() for i in range(3))
gz=base64.b64decode(b64); assert hashlib.sha256(gz).hexdigest()==EXPECTED
raw=gzip.decompress(gz)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf: tf.extractall(HERE/'src')
print(EXPECTED)
