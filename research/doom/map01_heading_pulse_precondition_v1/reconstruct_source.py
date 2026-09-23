from pathlib import Path
import base64,gzip,tarfile,io,hashlib,json,sys
m=json.loads(Path('SOURCE_MANIFEST.json').read_text())
s=''.join(Path(f'source.part{i:02d}.b64').read_text() for i in range(4))
g=base64.b64decode(s)
assert hashlib.sha256(g).hexdigest()=='ff7c4c1515e9d4bb8bec2f9da0ef71386bbf5dc7c0715feea79edb3e66d628b9'
raw=gzip.decompress(g); out=Path(sys.argv[1] if len(sys.argv)>1 else 'readback'); out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:t.extractall(out)
for n,v in m.items():
 if n.startswith('_'): continue
 b=(out/n).read_bytes(); assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],n
print('ff7c4c1515e9d4bb8bec2f9da0ef71386bbf5dc7c0715feea79edb3e66d628b9')
