import argparse, base64, hashlib, io, json, lzma, tarfile
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('out'); a=ap.parse_args()
root=Path(__file__).parent; manifest=json.loads((root/'BUNDLE.json').read_text()); out=Path(a.out)
if out.exists(): raise SystemExit('destination exists')
parts=[]
for ent in manifest['parts']:
    b=(root/ent['name']).read_bytes()
    if hashlib.sha256(b).hexdigest()!=ent['sha256']: raise SystemExit('part hash mismatch: '+ent['name'])
    parts.append(b)
tar_bytes=lzma.decompress(base64.b64decode(b''.join(parts)))
if hashlib.sha256(tar_bytes).hexdigest()!=manifest['tar_sha256']: raise SystemExit('tar hash mismatch')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(tar_bytes),mode='r:') as tf:
    members=tf.getmembers()
    if len(members)!=manifest['member_count']: raise SystemExit('member count mismatch')
    tf.extractall(out,filter='data')
for rel,h in manifest['critical_sha256'].items():
    p=out/rel
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise SystemExit('critical mismatch: '+rel)
print(json.dumps({'members':manifest['member_count'],'tar_sha256':manifest['tar_sha256']},sort_keys=True))
