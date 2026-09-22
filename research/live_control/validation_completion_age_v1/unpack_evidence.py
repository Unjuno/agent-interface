"""Read-only artifact decoder; creates a NEW directory, never runs an experiment."""
from __future__ import annotations
import argparse, hashlib, io, json, lzma, tarfile
from pathlib import Path, PurePosixPath
HERE=Path(__file__).resolve().parent

def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument('destination',type=Path);a=ap.parse_args()
    destination=a.destination.resolve()
    if destination.exists():raise FileExistsError('Destination must not exist')
    manifest=json.loads((HERE/'ARCHIVE.json').read_text())
    chunks=[]
    for part in manifest['parts']:
        relative=PurePosixPath(part['path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Invalid part path')
        data=(HERE/relative).read_bytes()
        if len(data)!=part['bytes'] or hashlib.sha256(data).hexdigest()!=part['sha256']:raise ValueError('Part mismatch')
        chunks.append(data)
    archive=b''.join(chunks)
    if len(archive)!=manifest['archive_bytes'] or hashlib.sha256(archive).hexdigest()!=manifest['archive_sha256']:
        raise ValueError('Archive mismatch')
    decoder=lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw=decoder.decompress(archive,max_length=2*1024*1024)
    if not decoder.eof or decoder.unused_data:raise ValueError('Oversize or concatenated archive')
    content={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
        for member in tar.getmembers():
            path=PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or member.name in content:
                raise ValueError('Invalid/duplicate archive member')
            data=tar.extractfile(member).read()
            if len(data)!=member.size:raise ValueError('Truncated member')
            content[member.name]=data
    if len(content)!=manifest['member_count'] or sum(map(len,content.values()))!=manifest['member_bytes']:
        raise ValueError('Member inventory mismatch')
    freeze_bytes=(HERE/'FREEZE.json').read_bytes();freeze=json.loads(freeze_bytes)
    sources={'FREEZE.json':freeze_bytes}
    for name,digest in freeze['sha256'].items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid source path')
        data=lzma.decompress((HERE/'native.so.xz').read_bytes()) if name=='native.so' else (HERE/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Source mismatch: '+name)
        sources[name]=data
    if set(sources)&set(content):raise ValueError('Evidence may not replace frozen source')
    destination.mkdir()
    for name,data in {**sources,**content}.items():
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(data)
    print(json.dumps({'destination':str(destination),'source_files':len(sources),'evidence_files':len(content),
                      'archive_sha256':manifest['archive_sha256'],'executed_experiment':False},sort_keys=True))
if __name__=='__main__':main()
