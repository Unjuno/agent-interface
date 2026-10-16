from pathlib import Path
import base64,gzip,hashlib,io,json,tarfile
r=Path(__file__).parent;m=json.loads((r/'SOURCE_MANIFEST.json').read_text())
parts=[]
for x in m['chunks']:
 b=(r/x['name']).read_bytes();assert len(b)==x['chars'];assert hashlib.sha256(b).hexdigest()==x['sha256'];parts.append(b)
b64=b''.join(parts);assert len(b64)==m['base64_chars'];assert hashlib.sha256(b64).hexdigest()==m['base64_sha256']
a=base64.b64decode(b64,validate=True);assert len(a)==m['archive_bytes'];assert hashlib.sha256(a).hexdigest()==m['archive_sha256']
raw=gzip.decompress(a);out=r/'reconstructed_unique';out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:tf.extractall(out,filter='data')
for n,v in m['files'].items():
 b=(out/n).read_bytes();assert len(b)==v['bytes'];assert hashlib.sha256(b).hexdigest()==v['sha256']
print('PASS',len(m['files']))
