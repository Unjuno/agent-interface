import base64, hashlib, json, lzma, tarfile, io, sys
from pathlib import Path
root=Path(__file__).resolve().parent
out=Path(sys.argv[1])
if out.exists(): raise SystemExit('destination_exists')
m=json.loads((root/'SOURCE_CAPSULE.json').read_text())
xz=base64.b64decode((root/'SOURCE_CAPSULE.b64').read_text().strip(),validate=True)
assert hashlib.sha256(xz).hexdigest()==m['xz_sha256'] and len(xz)==m['xz_bytes']
tar=lzma.decompress(xz)
assert hashlib.sha256(tar).hexdigest()==m['tar_sha256'] and len(tar)==m['tar_bytes']
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
 names=tf.getnames(); expected=[x['path'] for x in m['members']]
 assert names==expected
 for item in tf:
  if not item.isfile() or '/' in item.name or item.name.startswith('.'): raise SystemExit('unsafe_member')
  data=tf.extractfile(item).read(); (out/item.name).write_bytes(data)
for item in m['members']:
 b=(out/item['path']).read_bytes(); assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
print(json.dumps({'restored':len(m['members']),'xz_sha256':m['xz_sha256']},sort_keys=True))
