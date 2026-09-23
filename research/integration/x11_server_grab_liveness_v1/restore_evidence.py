import base64,hashlib,io,json,lzma,tarfile,sys
from pathlib import Path
root=Path(__file__).resolve().parent; out=Path(sys.argv[1])
if out.exists(): raise SystemExit('destination_exists')
parts=json.loads((root/'PARTS.json').read_text()); manifest=json.loads((root/'EVIDENCE.json').read_text())
s=''.join((root/x['path']).read_text().strip() for x in parts['parts'])
xz=base64.b64decode(s,validate=True)
assert hashlib.sha256(xz).hexdigest()==manifest['xz_sha256'] and len(xz)==manifest['xz_bytes']
tar=lzma.decompress(xz); assert hashlib.sha256(tar).hexdigest()==manifest['tar_sha256'] and len(tar)==manifest['tar_bytes']
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
 names=tf.getnames(); expected=[x['path'] for x in manifest['members']]; assert names==expected
 for item in tf:
  p=Path(item.name)
  if not item.isfile() or p.is_absolute() or '..' in p.parts: raise SystemExit('unsafe_member')
  dst=out/p; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(tf.extractfile(item).read())
for x in manifest['members']:
 b=(out/x['path']).read_bytes(); assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
print(json.dumps({'restored':len(manifest['members']),'xz_sha256':manifest['xz_sha256']},sort_keys=True))
