"""Data-only, digest-bound restore; never invokes a GUI allocation."""
import hashlib,io,json,lzma,shutil,sys,tarfile
from pathlib import Path,PurePosixPath
BASE=Path(__file__).resolve().parent

def unpack(manifest,destination):
    m=json.loads(manifest.read_text());chunks=[]
    for entry in m['parts']:
        data=(BASE/entry['name']).read_bytes()
        if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError('part integrity')
        chunks.append(data)
    data=b''.join(chunks)
    if len(data)!=m['archive_bytes'] or hashlib.sha256(data).hexdigest()!=m['archive_sha256']:
        raise ValueError('archive integrity')
    decoder=lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw=decoder.decompress(data,max_length=64*1024*1024+1)
    if len(raw)>64*1024*1024 or not decoder.eof or decoder.unused_data:raise ValueError('expansion bound')
    seen=set()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        for member in archive:
            p=PurePosixPath(member.name)
            if not member.isfile() or p.is_absolute() or '..' in p.parts or str(p)!=member.name or '\\' in member.name:
                raise ValueError('unsafe member')
            if member.name in seen or member.name not in m['members']:raise ValueError('member set')
            seen.add(member.name);data=archive.extractfile(member).read()
            if hashlib.sha256(data).hexdigest()!=m['members'][member.name]:raise ValueError('member digest')
            q=destination.joinpath(*p.parts);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as stream:stream.write(data)
    if seen!=set(m['members']):raise ValueError('missing member')
    return len(seen)

def restore(destination):
    dst=Path(destination)
    if dst.exists():raise ValueError('destination must be new')
    dst.mkdir(parents=True);n=unpack(BASE/'SOURCE.json',dst)
    shutil.copytree(BASE/'vendor',dst/'vendor')
    freeze=json.loads((dst/'FREEZE.json').read_text())
    for name,h in freeze['sha256'].items():
        if hashlib.sha256((dst/name).read_bytes()).hexdigest()!=h:raise ValueError('source:'+name)
    if (BASE/'EVIDENCE.json').exists():n+=unpack(BASE/'EVIDENCE.json',dst)
    return dict(restored_members=n,frozen_source_files=len(freeze['sha256']))
if __name__=='__main__':print(json.dumps(restore(sys.argv[1]),sort_keys=True))
