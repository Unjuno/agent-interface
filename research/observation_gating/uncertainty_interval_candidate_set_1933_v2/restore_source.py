import base64,hashlib,lzma,tarfile,io,sys
from pathlib import Path
EXPECTED='a6dbfbce0b20613a1df318e4bd5c284d777a8de4fbac57ef3f17a6fe8e029ef0'
b64=Path(__file__).with_name('SOURCE.tar.xz.b64').read_text()
data=base64.b64decode(''.join(b64.split()))
assert hashlib.sha256(data).hexdigest()==EXPECTED
out=Path(sys.argv[1])
out.mkdir(parents=True,exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data),mode='r:xz') as t: t.extractall(out)
print(EXPECTED)
