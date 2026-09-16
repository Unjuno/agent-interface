"""Verify and unpack compact evidence. Python 3.12+; never runs a GUI."""
from pathlib import Path, PurePosixPath
import hashlib, io, json, sys, tarfile

def main():
    here = Path(__file__).resolve().parent
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((here / 'manifest.json').read_text())
    pieces = []
    for part in manifest['parts']:
        name = PurePosixPath(part['path'])
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('invalid part path')
        data = (here / str(name)).read_bytes()
        identity = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256'] or identity != part['git_blob']:
            raise ValueError('part integrity mismatch: ' + str(name))
        pieces.append(data)
    archive = b''.join(pieces)
    if len(archive) != manifest['archive_bytes'] or hashlib.sha256(archive).hexdigest() != manifest['archive_sha256']:
        raise ValueError('archive integrity mismatch')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:xz') as source:
        members = source.getmembers()
        if sum(item.size for item in members) > 10_000_000:
            raise ValueError('unexpected archive size')
        for item in members:
            name = PurePosixPath(item.name)
            if not item.isfile() or name.is_absolute() or '..' in name.parts:
                raise ValueError('invalid archive entry')
        output.mkdir(parents=True)
        source.extractall(output, members=members, filter='data')
    print('PASS_COMPACT_ARCHIVE_RECONSTRUCTION', output)
    print('Run study/verify_witness.py separately on each witness-01/02/03.json.')
    print('Bulk raw traversal and screenshots are not in this compact archive; see RETENTION.json.')

if __name__ == '__main__':
    main()
