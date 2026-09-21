"""Restore verified research bytes into a NEW directory; never execute a study."""
import argparse
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

ROOT = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def restore(destination, source=ROOT):
    destination, source = Path(destination), Path(source)
    if destination.exists() or destination.is_symlink():
        raise ValueError('DESTINATION_EXISTS')
    m = json.loads((source / 'EVIDENCE.json').read_bytes())
    encoded = []
    for part in m['parts']:
        name = part['name']
        if Path(name).name != name or not name.endswith('.b64'):
            raise ValueError('PART_NAME')
        data = (source / name).read_bytes()
        if len(data) != part['bytes'] or digest(data) != part['sha256']:
            raise ValueError('PART_HASH:' + name)
        encoded.append(data.strip())
    archive = base64.b64decode(b''.join(encoded), validate=True)
    if len(archive) != m['archive_bytes'] or digest(archive) != m['archive_sha256']:
        raise ValueError('ARCHIVE_HASH')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = decoder.decompress(archive, max_length=m['tar_bytes'] + 1)
    if len(data) != m['tar_bytes'] or not decoder.eof or decoder.unused_data:
        raise ValueError('ARCHIVE_LENGTH')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as bundle:
        for entry in bundle.getmembers():
            path = PurePosixPath(entry.name)
            if (not entry.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != entry.name or entry.name in files):
                raise ValueError('MEMBER_PATH_OR_TYPE')
            files[entry.name] = bundle.extractfile(entry).read()
    if len(files) != m['member_count'] or digest(files['MEMBERS.json']) != m['members_manifest_sha256']:
        raise ValueError('MEMBER_MANIFEST')
    entries = json.loads(files['MEMBERS.json'])
    if set(files) != set(entries) | {'MEMBERS.json'}:
        raise ValueError('MEMBER_SET')
    for name, check in entries.items():
        if len(files[name]) != check['bytes'] or digest(files[name]) != check['sha256']:
            raise ValueError('MEMBER_HASH:' + name)
    if sum(map(len, files.values())) != m['total_member_bytes']:
        raise ValueError('TOTAL_BYTES')
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as output:
            output.write(value)
    return {'status': 'PASS_RESTORE', 'members': len(files), 'bytes': sum(map(len, files.values())),
            'archive_sha256': digest(archive)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(args.destination), indent=2, sort_keys=True))
