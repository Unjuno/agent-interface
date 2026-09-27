"""Bounded data-only extraction. Never imports/executes archived experiment code."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path,PurePosixPath
import tarfile

MAX_COMPRESSED=1_000_000
MAX_TAR=32*1024*1024
MAX_FILES=200

def require(ok,message):
    if not ok:raise ValueError(message)

def digest(b):return hashlib.sha256(b).hexdigest()

def restore(package_dir,target):
    package_dir=Path(package_dir);target=Path(target)
    require(not target.exists(),'destination exists')
    package=json.loads((package_dir/'PACK.json').read_text())
    require(package['format']=='tar-xz-v1','unsupported format')
    chunks=[];total=0
    for entry in package['parts']:
        name=entry['name'];require(PurePosixPath(name).name==name,'invalid part name')
        b=(package_dir/name).read_bytes();total+=len(b)
        require(total<=MAX_COMPRESSED,'compressed size limit')
        require(len(b)==entry['bytes'] and digest(b)==entry['sha256'],'part integrity')
        chunks.append(b)
    compressed=b''.join(chunks)
    require(digest(compressed)==package['archive_sha256'],'archive integrity')
    d=lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw=d.decompress(compressed,max_length=MAX_TAR+1)
    require(len(raw)<=MAX_TAR and d.eof and not d.unused_data,'expanded size/trailing data')
    require(len(raw)==package['tar_bytes'] and digest(raw)==package['tar_sha256'],'tar integrity')
    entries={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
        members=tar.getmembers()
        require(len(members)<=MAX_FILES,'file count limit')
        for m in members:
            name=m.name;path=PurePosixPath(name)
            require(m.isfile(),'non-regular archive member')
            require(name and not path.is_absolute() and '\\' not in name and
                    all(p not in ('','..','.') for p in name.split('/')),'unsafe member name')
            require(name not in entries,'duplicate member')
            require(0<=m.size<=12*1024*1024,'member size limit')
            f=tar.extractfile(m)
            require(f is not None,'member unreadable')
            with f:b=f.read()
            require(len(b)==m.size,'member length')
            entries[name]=b
    require(len(entries)==package['member_count'],'member count mismatch')
    require(set(entries)==set(package['members']),'member inventory')
    for name,b in entries.items():
        expected=package['members'][name]
        require(len(b)==expected['bytes'] and digest(b)==expected['sha256'],'member integrity')
        for parent in PurePosixPath(name).parents:
            require(str(parent) not in entries,'file/directory collision')
    # Validate the whole archive before creating any output file.
    target.mkdir(parents=False,exist_ok=False)
    for name,b in entries.items():
        p=target/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(b)
    return {'files':len(entries),'bytes':sum(map(len,entries.values())),
            'archive_sha256':digest(compressed),'executes_archive_code':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args()
    print(json.dumps(restore(Path(__file__).resolve().parent,a.destination),sort_keys=True))
