"""Bounded data-only reconstruction; refuses an existing destination."""
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys


def unique(pairs):
    d={}
    for key,value in pairs:
        if key in d: raise ValueError('DUPLICATE_JSON_KEY')
        d[key]=value
    return d


def restore(source,destination):
    source=Path(source);destination=Path(destination)
    if destination.exists(): raise ValueError('DESTINATION_EXISTS')
    manifest=json.loads((source/'PACKAGE.json').read_text(),object_pairs_hook=unique)
    if manifest['schema']!='text-capsule-v1': raise ValueError('SCHEMA')
    if type(manifest['expanded_bytes']) is not int or not 0<manifest['expanded_bytes']<=2000000: raise ValueError('SIZE')
    if type(manifest['files']) is not int or not 0<manifest['files']<=200: raise ValueError('COUNT')
    parts=manifest['parts']
    if not 0<len(parts)<=32 or len({p['path'] for p in parts})!=len(parts): raise ValueError('PARTS')
    chunks=[]
    for part in parts:
        path=PurePosixPath(part['path'])
        if len(path.parts)!=1 or path.is_absolute() or '..' in path.parts: raise ValueError('PART_PATH')
        raw=(source/path.name).read_bytes()
        if len(raw)>10000 or hashlib.sha256(raw).hexdigest()!=part['sha256']: raise ValueError('PART_HASH')
        chunks.append(raw.strip())
    compressed=base64.b64decode(b''.join(chunks),validate=True)
    if len(compressed)!=manifest['compressed_bytes'] or hashlib.sha256(compressed).hexdigest()!=manifest['compressed_sha256']: raise ValueError('COMPRESSED_HASH')
    decoder=lzma.LZMADecompressor(memlimit=134217728)
    raw=decoder.decompress(compressed,max_length=manifest['expanded_bytes']+1)
    if not decoder.eof or decoder.unused_data or len(raw)!=manifest['expanded_bytes'] or hashlib.sha256(raw).hexdigest()!=manifest['expanded_sha256']: raise ValueError('EXPANDED_HASH')
    files=json.loads(raw,object_pairs_hook=unique)
    if len(files)!=manifest['files'] or set(files)!=set(manifest['member_sha256']): raise ValueError('MEMBERS')
    for name,text in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path)!=name or not name or type(text) is not str: raise ValueError('MEMBER_PATH')
        if hashlib.sha256(text.encode()).hexdigest()!=manifest['member_sha256'][name]: raise ValueError('MEMBER_HASH')
    destination.mkdir(parents=False,exist_ok=False)
    for name,text in files.items():
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8',newline='') as f:f.write(text)
    return len(files)


if __name__=='__main__':
    print(restore(Path(__file__).resolve().parent,sys.argv[1]))
