"""Verify and restore retained evidence; never import or execute experiment code."""
import hashlib,io,json,lzma,sys,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
MAX_TAR=20_000_000

def safe(name):
    p=PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name:
        raise ValueError('unsafe member name')
    return p

def unpack(out):
    out=Path(out)
    if out.exists(): raise ValueError('destination exists')
    m=json.loads((ROOT/'CAPSULE.json').read_text())
    if type(m['tar_bytes']) is not int or not 0<m['tar_bytes']<=MAX_TAR:
        raise ValueError('size bound')
    blocks=[]
    for q in m['parts']:
        p=safe(q['path']);data=(ROOT/str(p)).read_bytes()
        if len(data)!=q['bytes'] or hashlib.sha256(data).hexdigest()!=q['sha256']:
            raise ValueError('part integrity')
        blocks.append(data)
    packed=b''.join(blocks)
    if len(packed)!=m['archive_bytes'] or hashlib.sha256(packed).hexdigest()!=m['archive_sha256']:
        raise ValueError('archive integrity')
    dec=lzma.LZMADecompressor();raw=dec.decompress(packed,max_length=MAX_TAR+1)
    if not dec.eof or dec.unused_data or len(raw)!=m['tar_bytes'] or hashlib.sha256(raw).hexdigest()!=m['tar_sha256']:
        raise ValueError('expanded integrity')
    records={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:
        for member in t:
            name=str(safe(member.name))
            if not member.isfile() or name in records:raise ValueError('member type/duplicate')
            f=t.extractfile(member)
            if f is None:raise ValueError('member unreadable')
            data=f.read()
            if len(data)!=member.size:raise ValueError('member size')
            records[name]=data
    if len(records)!=m['files'] or sum(map(len,records.values()))!=m['file_bytes']:
        raise ValueError('member accounting')
    out.mkdir(parents=True,exist_ok=False)
    for name,data in records.items():
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    return {'files':len(records),'file_bytes':m['file_bytes'],'archive_sha256':m['archive_sha256']}

if __name__=='__main__':print(json.dumps(unpack(sys.argv[1]),sort_keys=True))
