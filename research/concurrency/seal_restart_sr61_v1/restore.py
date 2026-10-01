"""Bounded data-only restore; destination parent must be trusted. No study runs."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

LIMIT = 64 * 1024 * 1024


def restore(manifest_path, archive_path, destination):
    manifest = json.loads(Path(manifest_path).read_text())
    data = Path(archive_path).read_bytes()
    if len(data) != manifest['archive_bytes']:
        raise ValueError('archive_size')
    if hashlib.sha256(data).hexdigest() != manifest['archive_sha256']:
        raise ValueError('archive_hash')
    dec = lzma.LZMADecompressor(memlimit=LIMIT)
    raw = dec.decompress(data, max_length=LIMIT + 1)
    if len(raw) > LIMIT or not dec.eof or dec.unused_data:
        raise ValueError('archive_expansion')
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as tf:
        for entry in tf:
            name = PurePosixPath(entry.name)
            if (not entry.isfile() or name.is_absolute() or '..' in name.parts
                    or str(name) != entry.name or entry.name in members):
                raise ValueError('member_type_or_path')
            if entry.size > LIMIT or len(members) >= 4000:
                raise ValueError('member_limit')
            blob = tf.extractfile(entry).read()
            if hashlib.sha256(blob).hexdigest() != manifest['members'].get(entry.name):
                raise ValueError('member_hash:' + entry.name)
            members[entry.name] = blob
    if set(members) != set(manifest['members']):
        raise ValueError('member_set')
    out = Path(destination)
    out.mkdir(parents=False, exist_ok=False)
    for name, blob in members.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(blob)
    return {'files': len(members), 'bytes': sum(map(len, members.values())),
            'archive_sha256': manifest['archive_sha256']}


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit('usage: restore.py MANIFEST ARCHIVE NEW_DIRECTORY')
    print(json.dumps(restore(*sys.argv[1:]), sort_keys=True))
