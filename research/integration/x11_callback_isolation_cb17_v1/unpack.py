"""Verify and restore data only; never run the archived source."""
import base64,hashlib,json,sys,lzma
from pathlib import Path,PurePosixPath
manifest=Path(sys.argv[1]).resolve();out=Path(sys.argv[2])
m=json.loads(manifest.read_text());encoded=[]
for part in m['parts']:
    p=PurePosixPath(part['name'])
    if len(p.parts)!=1 or p.is_absolute():raise ValueError('part path')
    b=(manifest.parent/str(p)).read_bytes()
    if hashlib.sha256(b).hexdigest()!=part['sha256']:raise ValueError('part digest')
    encoded.append(b)
compressed=base64.b64decode(b''.join(encoded))
if hashlib.sha256(compressed).hexdigest()!=m['archive_sha256']:raise ValueError('archive digest')
if not 0<m['json_bytes']<=8000000:raise ValueError('size bound')
d=lzma.LZMADecompressor();raw=d.decompress(compressed,max_length=m['json_bytes']+1)
if len(raw)!=m['json_bytes'] or not d.eof or d.unused_data:raise ValueError('expanded size')
if hashlib.sha256(raw).hexdigest()!=m['json_sha256']:raise ValueError('JSON digest')
payload=json.loads(raw)
if set(payload['files'])!=set(payload['sha256']) or len(payload['files'])!=m['files_count']:raise ValueError('inventory')
for name,text in payload['files'].items():
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or not p.parts:raise ValueError('member path')
    if hashlib.sha256(text.encode()).hexdigest()!=payload['sha256'][name]:raise ValueError('member digest')
out.mkdir(parents=True,exist_ok=False)
for name,text in payload['files'].items():
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
print(json.dumps({'files':len(payload['files']),'archive_sha256':m['archive_sha256']}))
