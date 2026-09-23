import base64,hashlib,json,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).parent
M=json.loads((HERE/'CHUNK_MANIFEST.json').read_text())
parts=[]
for row in M['chunks']:
 p=HERE/'chunks'/row['name']; data=p.read_bytes()
 if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise SystemExit(row['name'])
 parts.append(data)
b=b''.join(parts)
if len(b)!=M['joined_base64_bytes'] or hashlib.sha256(b).hexdigest()!=M['joined_base64_sha256']:raise SystemExit('joined_base64')
raw=base64.b64decode(b)
if len(raw)!=M['tar_gz_bytes'] or hashlib.sha256(raw).hexdigest()!=M['tar_gz_sha256']:raise SystemExit('tar')
with tempfile.TemporaryDirectory() as td:
 tpath=Path(td)/'s.tgz';tpath.write_bytes(raw)
 with tarfile.open(tpath,'r:gz') as t:t.extractall(td,filter='data')
 print('OK',sorted(p.name for p in Path(td).iterdir() if p.name!='s.tgz'))
