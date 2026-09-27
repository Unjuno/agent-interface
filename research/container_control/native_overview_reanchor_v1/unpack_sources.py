"""Restore exact research sources; only safe basenames, no automatic execution."""
import base64,hashlib,json,lzma,sys
from pathlib import Path
root=Path(__file__).resolve().parent;manifest=json.loads((root/'sources/manifest.json').read_text());parts=[]
for row in manifest['parts']:
    data=(root/'sources'/row['file']).read_bytes()
    if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('source part mismatch')
    parts.append(data.strip())
raw=lzma.decompress(base64.b64decode(b''.join(parts),validate=True))
if hashlib.sha256(raw).hexdigest()!=manifest['raw_sha256']:raise ValueError('source archive mismatch')
out=Path(sys.argv[1]) if len(sys.argv)>1 else root/'decoded';out.mkdir(parents=True,exist_ok=False)
for name,item in json.loads(raw).items():
    if Path(name).name!=name:raise ValueError('unsafe source name')
    data=item['utf8'].encode('utf-8')
    if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('source content mismatch')
    (out/name).write_bytes(data)
print('Restored',len(manifest['files']),'hash-verified source files into',out)
