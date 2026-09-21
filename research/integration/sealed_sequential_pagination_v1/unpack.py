"""Bounded data-only evidence restoration. Does not execute archived code."""
import hashlib,io,json,lzma,sys,tarfile
from pathlib import Path

def require(ok,msg):
    if not ok:raise ValueError(msg)

def main():
    root=Path(__file__).resolve().parent;meta=json.loads((root/'CAPSULE.json').read_text())
    out=Path(sys.argv[1]);require(not out.exists(),'DESTINATION_EXISTS')
    chunks=[]
    for spec in meta['parts']:
        p=root/spec['name'];b=p.read_bytes()
        require(len(b)==spec['bytes'] and hashlib.sha256(b).hexdigest()==spec['sha256'],'PART_MISMATCH')
        chunks.append(b)
    archive=b''.join(chunks);require(hashlib.sha256(archive).hexdigest()==meta['archive_sha256'],'ARCHIVE_MISMATCH')
    decoder=lzma.LZMADecompressor(memlimit=268435456);raw=decoder.decompress(archive,max_length=meta['tar_bytes']+1)
    require(decoder.eof and not decoder.unused_data and len(raw)==meta['tar_bytes'],'EXPANSION_MISMATCH')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
        entries=tar.getmembers();require(len(entries)==meta['member_count'],'MEMBER_COUNT')
        seen=set()
        for e in entries:
            p=Path(e.name)
            require(e.isfile() and not p.is_absolute() and '..' not in p.parts and e.name not in seen,'UNSAFE_MEMBER')
            seen.add(e.name)
        out.mkdir(parents=True)
        for e in entries:
            p=out/e.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tar.extractfile(e).read())
    print(json.dumps({'restored':len(entries),'archive_sha256':meta['archive_sha256'],'scope':'bytes only; does not change original HOLD'}))
if __name__=='__main__':main()
