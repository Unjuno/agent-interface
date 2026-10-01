"""Bounded data-only capsule restoration to an exclusively new directory."""
import base64, hashlib, json, lzma, sys
from pathlib import Path, PurePosixPath
manifest=Path(sys.argv[1]).resolve();out=Path(sys.argv[2])
m=json.loads(manifest.read_text());parts=[]
for p in m['parts']:
 data=(manifest.parent/p['path']).read_bytes()
 if hashlib.sha256(data).hexdigest()!=p['sha256']:raise ValueError('part hash')
 parts.append(data.strip())
archive=base64.b64decode(b''.join(parts),validate=True)
if hashlib.sha256(archive).hexdigest()!=m['archive_sha256']:raise ValueError('archive hash')
dec=lzma.LZMADecompressor(memlimit=64*1024*1024)
raw=dec.decompress(archive,max_length=16*1024*1024)
if not dec.eof or dec.unused_data or hashlib.sha256(raw).hexdigest()!=m['json_sha256']:raise ValueError('expansion/hash')
files=json.loads(raw)['files']
if len(files)!=m['files_count']:raise ValueError('file count')
for name in files:
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('path')
out.mkdir(parents=True,exist_ok=False)
for name,text in files.items():
 p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode('utf-8'))
print(json.dumps({'files':len(files),'archive_sha256':m['archive_sha256']}))
