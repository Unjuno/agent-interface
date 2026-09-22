"""Verify and restore a bounded data-only evidence archive; never runs a study."""
import argparse,hashlib,json,sys,tarfile
from pathlib import Path,PurePosixPath

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def restore(root,dest):
    meta=json.loads((root/'ARCHIVE.json').read_bytes())
    archive=root/meta['archive']
    b=archive.read_bytes()
    require(type(meta['bytes']) is int and len(b)==meta['bytes'] and sha(b)==meta['sha256'],'ARCHIVE_IDENTITY_MISMATCH')
    require(not dest.exists(),'DESTINATION_ALREADY_EXISTS')
    with tarfile.open(archive,'r:xz') as tf:
        members=tf.getmembers();names=[m.name for m in members]
        require(type(meta['files']) is int and len(members)==meta['files']<=5000,'MEMBER_COUNT')
        require(len(names)==len(set(names)),'DUPLICATE_MEMBER')
        total=0
        for m in members:
            p=PurePosixPath(m.name)
            require(m.isfile() and not p.is_absolute() and '..' not in p.parts and '\\' not in m.name,'UNSAFE_MEMBER')
            require(0<=m.size<=50000000,'MEMBER_SIZE');total+=m.size
        require(total<=150000000,'EXPANSION_BOUND')
        manifest=json.loads(tf.extractfile(meta['manifest']).read())
        expected={x['path']:x for x in manifest}
        require(len(expected)==len(manifest) and set(expected)|{meta['manifest']}==set(names),'MANIFEST_COVERAGE')
        # Check every byte before opening any destination file.
        for m in members:
            if m.name==meta['manifest']:continue
            data=tf.extractfile(m).read();row=expected[m.name]
            require(type(row['bytes']) is int and len(data)==row['bytes'] and sha(data)==row['sha256'],'MEMBER_HASH:'+m.name)
        dest.mkdir(parents=True,exist_ok=False)
        for m in members:
            p=dest/m.name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as out:out.write(tf.extractfile(m).read())
    return {'restored_files':len(members),'manifest_entries':len(manifest),'archive_sha256':sha(b),'runs_experiment':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:print(json.dumps(restore(Path(__file__).resolve().parent,a.out),sort_keys=True))
    except (ValueError,OSError,KeyError,TypeError,tarfile.TarError) as e:
        print(json.dumps({'status':'STOP_RESTORE','error':str(e)}));sys.exit(2)
