import base64,hashlib,json,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).parent;M=json.loads((HERE/'SOURCE_MANIFEST.json').read_text());b=(HERE/'source_bundle.b64').read_bytes()
if hashlib.sha256(b).hexdigest()!=M['base64_sha256']:raise SystemExit('base64')
raw=base64.b64decode(b)
if hashlib.sha256(raw).hexdigest()!=M['tar_gz_sha256']:raise SystemExit('tar')
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.tgz';p.write_bytes(raw)
 with tarfile.open(p,'r:gz') as t:t.extractall(td,filter='data')
 for n,s in M['files'].items():
  data=(Path(td)/n).read_bytes()
  if hashlib.sha256(data).hexdigest()!=s:raise SystemExit(n)
  (HERE/n).write_bytes(data)
print('OK',len(M['files']))
