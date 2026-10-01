"""Bounded data-only restoration into a new directory. Executes no study code."""
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys


def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError('duplicate key')
        out[k]=v
    return out


def digest(b):
    return hashlib.sha256(b).hexdigest()


def safe(name):
    p=PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or str(p)!=name:
        raise ValueError('noncanonical path')
    return p


def restore(manifest, destination):
    manifest=Path(manifest);destination=Path(destination)
    if destination.exists(): raise ValueError('new destination required')
    meta=json.loads(manifest.read_text(),object_pairs_hook=unique)
    if not 0<meta['compressed_size']<=1000000 or not 0<meta['plain_size']<=4000000:
        raise ValueError('size limit')
    text=b''
    for part in meta['parts']:
        name=safe(part['file'])
        if len(name.parts)!=1: raise ValueError('part must be sibling')
        p=manifest.parent/str(name)
        if p.is_symlink() or p.stat().st_size>20000: raise ValueError('part shape')
        b=p.read_bytes()
        if digest(b)!=part['sha256']: raise ValueError('part digest')
        text+=b.strip()
    archive=base64.b64decode(text,validate=True)
    if len(archive)!=meta['compressed_size'] or digest(archive)!=meta['archive_sha256']:
        raise ValueError('archive mismatch')
    decoder=lzma.LZMADecompressor(memlimit=67108864)
    plain=decoder.decompress(archive,max_length=meta['plain_size']+1)
    if not decoder.eof or decoder.unused_data or len(plain)!=meta['plain_size'] or digest(plain)!=meta['plain_sha256']:
        raise ValueError('expanded mismatch')
    mapping=json.loads(plain,object_pairs_hook=unique)
    if set(mapping)!=set(meta['files']): raise ValueError('member set')
    decoded={}
    for name,data in mapping.items():
        safe(name);b=data.encode('utf-8');spec=meta['files'][name]
        if len(b)!=spec['bytes'] or digest(b)!=spec['sha256']: raise ValueError('member mismatch')
        decoded[name]=b
    destination.mkdir(parents=True,exist_ok=False)
    for name,data in decoded.items():
        p=destination/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as out: out.write(data)
    return {'files':len(decoded),'bytes':sum(map(len,decoded.values())),'verified':True}


if __name__=='__main__':
    print(json.dumps(restore(sys.argv[1],sys.argv[2]),sort_keys=True))
