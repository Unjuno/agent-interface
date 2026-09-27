"""Verify and extract this finite evidence capsule. Never executes research code."""
from pathlib import Path
import argparse,hashlib,io,json,lzma,tarfile
ROOT=Path(__file__).resolve().parent
MAX_ARCHIVE=10_000_000
MAX_TAR=50_000_000
MAX_FILES=2000

def restore(out):
    out=Path(out).resolve()
    if out.exists():raise ValueError('DESTINATION_EXISTS')
    manifest=json.loads((ROOT/'CAPSULE.json').read_text())
    if manifest['archive']!='evidence.tar.xz':raise ValueError('ARCHIVE_NAME')
    data=(ROOT/'evidence.tar.xz').read_bytes()
    if len(data)>MAX_ARCHIVE or len(data)!=manifest['archive_bytes']:raise ValueError('ARCHIVE_SIZE')
    if hashlib.sha256(data).hexdigest()!=manifest['archive_sha256']:raise ValueError('ARCHIVE_DIGEST')
    dec=lzma.LZMADecompressor();raw=dec.decompress(data,max_length=MAX_TAR+1)
    if len(raw)>MAX_TAR or not dec.eof or dec.unused_data:raise ValueError('EXPANSION_BOUND')
    if len(raw)!=manifest['tar_bytes'] or hashlib.sha256(raw).hexdigest()!=manifest['tar_sha256']:raise ValueError('TAR_DIGEST')
    contents={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
        for member in tf:
            name=member.name;path=Path(name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or str(path)!=name or name in contents:raise ValueError('UNSAFE_MEMBER')
            if name not in manifest['members'] or len(contents)>=MAX_FILES:raise ValueError('MEMBER_LIST')
            info=manifest['members'][name]
            if member.size!=info['bytes']:raise ValueError('MEMBER_SIZE')
            value=tf.extractfile(member).read()
            if hashlib.sha256(value).hexdigest()!=info['sha256']:raise ValueError('MEMBER_DIGEST')
            contents[name]=value
    if set(contents)!=set(manifest['members']):raise ValueError('MISSING_MEMBER')
    out.mkdir(parents=True,exist_ok=False)
    for name,value in contents.items():
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(value)
    return {'files':len(contents),'archive_sha256':manifest['archive_sha256'],'output':str(out)}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out');args=ap.parse_args()
    print(json.dumps(restore(args.out),sort_keys=True))
