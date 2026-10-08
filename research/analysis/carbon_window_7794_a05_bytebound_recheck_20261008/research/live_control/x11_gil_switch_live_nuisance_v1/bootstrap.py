#!/usr/bin/env python3
import base64,hashlib,json,lzma,tarfile,io
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/'source_manifest.json').read_text())
s=''.join(p.read_text().strip() for p in sorted(root.glob('source.part*.b64')))
xz=base64.b64decode(s,validate=True)
assert len(xz)==m['xz_bytes'] and hashlib.sha256(xz).hexdigest()==m['xz_sha256']
tar=lzma.decompress(xz)
assert len(tar)==m['tar_bytes'] and hashlib.sha256(tar).hexdigest()==m['tar_sha256']
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
    for member in tf.getmembers():
        assert member.name in m['files'] and '/' not in member.name and '..' not in member.name
        data=tf.extractfile(member).read()
        meta=m['files'][member.name]
        assert len(data)==meta['bytes'] and hashlib.sha256(data).hexdigest()==meta['sha256']
        (root/member.name).write_bytes(data)
print(json.dumps({'ok':True,'files':len(m['files']),'xz_sha256':m['xz_sha256']}))
