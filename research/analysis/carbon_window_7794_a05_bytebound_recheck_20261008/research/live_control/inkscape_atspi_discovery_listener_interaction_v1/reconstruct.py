#!/usr/bin/env python3
import base64,hashlib,json,tarfile
from pathlib import Path
r=Path(__file__).resolve().parent
m=json.loads((r/'publication.json').read_text())
parts=[]
for meta in m['github_archive_storage']['parts']:
    p=r/meta['path']; b=p.read_bytes()
    assert len(b)==meta['bytes'], (p.name,len(b),meta['bytes'])
    assert hashlib.sha256(b).hexdigest()==meta['sha256'], p.name
    parts.append(b.decode())
raw=base64.b64decode(''.join(''.join(s.split()) for s in parts),validate=True)
assert len(raw)==m['archive_bytes']
assert hashlib.sha256(raw).hexdigest()==m['archive_sha256']
p=r/m['archive_path'];p.write_bytes(raw)
out=r/'reconstructed';out.mkdir(exist_ok=True)
with tarfile.open(p,'r:gz') as tf: tf.extractall(out,filter='data')
print({'ok':True,'parts':len(parts),'bytes':len(raw),'sha256':m['archive_sha256']})
