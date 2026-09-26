"""Restore retained UTF-8 files; never execute study code. New destination only."""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import json
import lzma
import sys


def restore(destination):
    root=Path(__file__).resolve().parent
    combined={}
    for pack in ('SOURCE_PACK.json','RESULT_PACK.json'):
        if not (root/pack).exists():
            if pack.startswith('SOURCE'):
                raise ValueError('missing source pack')
            continue
        meta=json.loads((root/pack).read_text())
        chunks=[]
        for name,h in meta['parts'].items():
            part=(root/name).read_bytes()
            if hashlib.sha256(part).hexdigest()!=h:
                raise ValueError('part hash '+name)
            chunks.append(part.strip())
        b=base64.b64decode(b''.join(chunks),validate=True)
        if len(b)!=meta['compressed_bytes'] or hashlib.sha256(b).hexdigest()!=meta['compressed_sha256']:
            raise ValueError('compressed hash')
        decoder=lzma.LZMADecompressor(memlimit=64*1024*1024)
        raw=decoder.decompress(b,max_length=10*1024*1024+1)
        if not decoder.eof or decoder.unused_data or len(raw)>10*1024*1024:
            raise ValueError('expansion limit or trailing bytes')
        if len(raw)!=meta['expanded_bytes'] or hashlib.sha256(raw).hexdigest()!=meta['expanded_sha256']:
            raise ValueError('expanded hash')
        data=json.loads(raw)
        if set(data)!=set(meta['files']):
            raise ValueError('member set')
        for name,text in data.items():
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or str(p)!=name or '\\' in name:
                raise ValueError('invalid member path')
            if not isinstance(text,str) or hashlib.sha256(text.encode()).hexdigest()!=meta['files'][name]:
                raise ValueError('member hash '+name)
            if name in combined:
                raise ValueError('overlapping members')
            combined[name]=text
    dest=Path(destination)
    dest.mkdir()  # Refuses an existing destination; trusted, quiescent parent.
    for name,text in combined.items():
        target=dest/name
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x',encoding='utf-8',newline='') as f:
            f.write(text)
    return len(combined)


if __name__=='__main__':
    print(json.dumps({'restored_files':restore(sys.argv[1]),'study_executed':False}))
