"""Restore a bounded research archive into a NEW directory; execute nothing."""
from __future__ import annotations
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile


def sha(b):return hashlib.sha256(b).hexdigest()

def restore(source:Path,destination:Path):
    if destination.exists():raise FileExistsError('destination must not exist')
    meta=json.loads((source/'CAPSULE.json').read_text())
    if meta['format']!='xz-ustar-v1' or not 1<=len(meta['parts'])<=20:raise ValueError('format/part count')
    chunks=[]
    for i,part in enumerate(meta['parts']):
        if part['file']!=f'capsule-{i:02d}.bin':raise ValueError('part name')
        data=(source/part['file']).read_bytes()
        if len(data)!=part['bytes'] or sha(data)!=part['sha256']:raise ValueError('part integrity')
        chunks.append(data)
    packed=b''.join(chunks)
    if len(packed)>500000 or len(packed)!=meta['compressed_bytes'] or sha(packed)!=meta['compressed_sha256']:raise ValueError('capsule integrity')
    dec=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024*1024)
    expanded=dec.decompress(packed,max_length=8*1024*1024+1)
    if len(expanded)>8*1024*1024 or not dec.eof or dec.unused_data:raise ValueError('expansion bound/framing')
    if len(expanded)!=meta['tar_bytes'] or sha(expanded)!=meta['tar_sha256']:raise ValueError('expanded identity')
    ready=[];seen=set();total=0
    with tarfile.open(fileobj=io.BytesIO(expanded),mode='r:') as archive:
        members=archive.getmembers()
        if len(members)!=meta['files'] or len(members)>500:raise ValueError('file denominator')
        for member in members:
            name=member.name;path=PurePosixPath(name)
            if not member.isfile() or not name or path.is_absolute() or '..' in path.parts or '\\' in name or str(path)!=name or name in seen:raise ValueError('member path/type')
            seen.add(name);data=archive.extractfile(member).read()
            if len(data)!=member.size:raise ValueError('member length')
            total+=len(data);ready.append((name,data))
    if total!=meta['member_bytes'] or total>8*1024*1024:raise ValueError('member byte denominator')
    for name in seen:
        if any(str(parent) in seen for parent in PurePosixPath(name).parents):raise ValueError('file/directory conflict')
    destination.mkdir(parents=True,exist_ok=False)
    for name,data in ready:
        out=destination/name;out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('xb') as stream:stream.write(data)
    return {'files':len(ready),'member_bytes':total,'compressed_sha256':sha(packed),'executes_code':False}

if __name__=='__main__':
    print(json.dumps(restore(Path(__file__).resolve().parent,Path(sys.argv[1]).resolve()),indent=2))
