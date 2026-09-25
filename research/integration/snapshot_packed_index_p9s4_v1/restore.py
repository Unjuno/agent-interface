"""Data-only bounded restoration; never runs the archived experiment."""
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

def restore(package, destination):
    package, destination = Path(package), Path(destination)
    if destination.exists():
        raise ValueError('DESTINATION_EXISTS')
    meta = json.loads((package / 'PACK.json').read_text())
    chunks = []
    for part in meta['parts']:
        name = PurePosixPath(part['name'])
        if len(name.parts) != 1 or name.name in ('.', '..'):
            raise ValueError('PART_PATH')
        value = (package / name.name).read_bytes()
        if len(value) != part['bytes'] or hashlib.sha256(value).hexdigest() != part['sha256']:
            raise ValueError('PART_HASH')
        chunks.append(value.strip())
    raw = base64.b64decode(b''.join(chunks), validate=True)
    if len(raw) != meta['archive_bytes'] or hashlib.sha256(raw).hexdigest() != meta['archive_sha256']:
        raise ValueError('ARCHIVE_HASH')
    limit = meta['tar_bytes']
    if type(limit) is not int or not 0 < limit <= 64 * 1024 * 1024:
        raise ValueError('EXPANSION_LIMIT')
    dec = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = dec.decompress(raw, max_length=limit + 1)
    if len(data) != limit or not dec.eof or dec.unused_data:
        raise ValueError('EXPANSION_SIZE')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as arc:
        for item in arc.getmembers():
            path = PurePosixPath(item.name)
            if not item.isfile() or path.is_absolute() or '..' in path.parts or str(path) != item.name or not path.parts:
                raise ValueError('MEMBER_PATH')
            if item.name in files:
                raise ValueError('DUPLICATE_MEMBER')
            value = arc.extractfile(item).read()
            if len(value) != item.size:
                raise ValueError('MEMBER_SIZE')
            files[item.name] = value
    if len(files) != meta['members']:
        raise ValueError('MEMBER_COUNT')
    destination.mkdir(parents=True)
    for name, value in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as out:
            out.write(value)
    return {'members':len(files), 'bytes':sum(map(len, files.values())), 'archive_sha256':meta['archive_sha256']}

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: restore.py PACKAGE_DIRECTORY NEW_DESTINATION')
    print(json.dumps(restore(*sys.argv[1:]), sort_keys=True))
