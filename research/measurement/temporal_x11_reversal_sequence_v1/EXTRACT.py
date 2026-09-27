from pathlib import Path
import base64,gzip,io,tarfile,hashlib
HERE=Path(__file__).resolve().parent
EXPECTED='78c83f8be655a813aaca172aad346dac6aa7f074fbaced137116e0060620f30e'
gz=base64.b64decode((HERE/'SOURCE_BUNDLE.b64').read_bytes())
assert hashlib.sha256(gz).hexdigest()==EXPECTED
with tarfile.open(fileobj=io.BytesIO(gzip.decompress(gz)),mode='r:') as tf:
    tf.extractall(HERE/'src')
print(EXPECTED)
