"""Verify/extract only. Never runs archived experiment code. Fresh destination only."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile


def restore(destination):
    here=Path(__file__).resolve().parent
    manifest=json.loads((here/'CAPSULE.json').read_bytes())
    archive=here/'EVIDENCE.tar.xz'
    data=archive.read_bytes()
    if len(data)!=manifest['archive_bytes'] or hashlib.sha256(data).hexdigest()!=manifest['archive_sha256']:
        raise ValueError('ARCHIVE_BYTE_IDENTITY')
    specs=manifest['members']
    if len(specs)!=manifest['member_count'] or sum(x['bytes'] for x in specs.values())!=manifest['expanded_bytes']:
        raise ValueError('MANIFEST_COUNTS')
    if len(specs)>5000 or manifest['expanded_bytes']>32*1024*1024:
        raise ValueError('EXPANSION_BOUND')
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    seen=set()
    with tarfile.open(archive,'r:xz') as t:
        for item in t:
            path=PurePosixPath(item.name)
            if (not item.isfile() or path.is_absolute() or '..' in path.parts
                    or item.name in seen or item.name not in specs):
                raise ValueError('UNEXPECTED_MEMBER')
            spec=specs[item.name]
            if type(spec['bytes']) is not int or item.size!=spec['bytes']:
                raise ValueError('MEMBER_LENGTH')
            with t.extractfile(item) as f: content=f.read(spec['bytes']+1)
            if len(content)!=spec['bytes'] or hashlib.sha256(content).hexdigest()!=spec['sha256']:
                raise ValueError('MEMBER_DIGEST')
            target=out/path;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(content)
            seen.add(item.name)
    if seen!=set(specs):raise ValueError('MISSING_MEMBER')
    print(json.dumps({'restored_files':len(seen),'expanded_bytes':manifest['expanded_bytes'],
                      'archive_sha256':manifest['archive_sha256'],'pass':True},sort_keys=True))

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: python restore.py <fresh-output-directory>')
    restore(sys.argv[1])
