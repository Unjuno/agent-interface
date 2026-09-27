"""Restore verified regular files only; never execute the research allocation."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile


def restore(manifest_path, destination):
    manifest_path, destination = Path(manifest_path), Path(destination)
    m = json.loads(manifest_path.read_text())
    if destination.exists():
        raise ValueError('destination must not exist')
    chunks = []
    for item in m['parts']:
        name = PurePosixPath(item['path'])
        if name.is_absolute() or len(name.parts) != 1:
            raise ValueError('invalid part path')
        b = (manifest_path.parent / str(name)).read_bytes()
        if type(item['size']) is not int or len(b) != item['size']:
            raise ValueError('part length')
        oid = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
        if oid != item['git_blob']:
            raise ValueError('part blob')
        chunks.append(b)
    archive = b''.join(chunks)
    if len(archive) != m['archive_bytes'] or hashlib.sha256(archive).hexdigest() != m['archive_sha256']:
        raise ValueError('archive binding')
    decoder = lzma.LZMADecompressor()
    data = decoder.decompress(archive, max_length=32 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('oversized or trailing XZ')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as t:
        members = t.getmembers()
        names = set()
        if len(members) != m['members']:
            raise ValueError('member count')
        for member in members:
            name = PurePosixPath(member.name)
            if not member.isfile() or name.is_absolute() or '..' in name.parts or str(name) in names:
                raise ValueError('unsafe or duplicate member')
            names.add(str(name))
        destination.mkdir()
        for member in members:
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(t.extractfile(member).read())
    print(json.dumps({'members':len(members),'archive_sha256':m['archive_sha256']}))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: unpack.py MANIFEST.json NEW_DESTINATION')
    restore(sys.argv[1], sys.argv[2])
