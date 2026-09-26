"""Restore bounded data files only. Does not execute archived code or experiments."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile


def restore(out):
    here = Path(__file__).resolve().parent
    pack = json.loads((here/'PACK.json').read_text())
    parts = []
    for entry in pack['parts']:
        if Path(entry['path']).name != entry['path']:
            raise ValueError('invalid part name')
        data = (here/entry['path']).read_bytes()
        if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError('part integrity')
        parts.append(data)
    archive = b''.join(parts)
    if len(archive)!=pack['archive_bytes'] or hashlib.sha256(archive).hexdigest()!=pack['archive_sha256']:
        raise ValueError('archive integrity')
    dec=lzma.LZMADecompressor(memlimit=134217728)
    raw=dec.decompress(archive,max_length=4194305)
    if len(raw)>4194304 or not dec.eof or dec.unused_data:
        raise ValueError('expanded bound')
    if len(raw)!=pack['tar_bytes'] or hashlib.sha256(raw).hexdigest()!=pack['tar_sha256']:
        raise ValueError('tar integrity')
    files=[]
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
        for m in tar.getmembers():
            name=PurePosixPath(m.name)
            if not m.isfile() or name.is_absolute() or '..' in name.parts or '\\' in m.name:
                raise ValueError('invalid member')
            if len(files)>=300 or m.size>1500000:
                raise ValueError('member bound')
            b=tar.extractfile(m).read()
            if len(b)!=m.size:
                raise ValueError('member extent')
            files.append((name,b))
    if len(files)!=pack['file_count'] or len(set(str(n) for n,b in files))!=len(files):
        raise ValueError('member count or duplicate')
    if sum(len(b) for n,b in files)!=pack['file_bytes']:
        raise ValueError('total file bytes')
    out.mkdir(parents=True,exist_ok=False)
    for name,b in files:
        path=out/str(name)
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as target: target.write(b)
    print(json.dumps({'restored':len(files),'bytes':sum(len(b) for n,b in files),
                      'archive_sha256':pack['archive_sha256']},sort_keys=True))


if __name__=='__main__':
    restore(Path(sys.argv[1]))
