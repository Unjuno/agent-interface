import base64,hashlib,tarfile,io,sys
from pathlib import Path
EXPECTED='436ef8be1267dcb294a1ae75867ad062961ca4fbbb4a9435d11906b5d6bcb84e'
b64=Path(__file__).with_name('EVIDENCE.tar.xz.b64').read_text()
data=base64.b64decode(''.join(b64.split()))
assert hashlib.sha256(data).hexdigest()==EXPECTED
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data),mode='r:xz') as t:t.extractall(out)
print(EXPECTED)
