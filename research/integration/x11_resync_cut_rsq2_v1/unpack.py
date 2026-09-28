"""Data-only bounded restoration into a new trusted directory; never executes study code."""
import base64,hashlib,json,lzma,sys
from pathlib import Path,PurePosixPath

def restore(manifest,destination):
    manifest=Path(manifest);destination=Path(destination)
    if destination.exists():raise ValueError('destination must not exist')
    m=json.loads(manifest.read_text());text=[]
    for part in m['parts']:
        name=part['path']
        if PurePosixPath(name).name!=name:raise ValueError('invalid part path')
        b=(manifest.parent/name).read_bytes()
        if hashlib.sha256(b).hexdigest()!=part['sha256']:raise ValueError('part hash')
        text.append(b.strip())
    z=base64.b64decode(b''.join(text),validate=True)
    if len(z)!=m['archive_bytes'] or hashlib.sha256(z).hexdigest()!=m['archive_sha256']:raise ValueError('archive hash')
    if not 0<m['raw_bytes']<=16000000:raise ValueError('expansion bound')
    d=lzma.LZMADecompressor(memlimit=256000000);raw=d.decompress(z,max_length=m['raw_bytes']+1)
    if not d.eof or d.unused_data or len(raw)!=m['raw_bytes'] or hashlib.sha256(raw).hexdigest()!=m['raw_sha256']:raise ValueError('expanded bytes')
    files=json.loads(raw)
    if len(files)!=m['files_count'] or len(files)>3000:raise ValueError('file count')
    for n,v in files.items():
        p=PurePosixPath(n)
        if not n or p.is_absolute() or '..' in p.parts or '\\' in n or not isinstance(v,str):raise ValueError('member path/type')
    destination.mkdir()
    for n,v in files.items():
        p=destination/n;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('x',encoding='utf-8',newline='') as f:f.write(v)
    return {'files':len(files),'archive_sha256':m['archive_sha256']}
if __name__=='__main__':print(json.dumps(restore(sys.argv[1],sys.argv[2]),sort_keys=True))
