"""Verify and unpack retained Issue #3945 evidence. Never launches the study."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

EXPECTED = '01e398fd63598fa319877b4fe68c0339c6ec7c348b66349166b4b636687787e2'


def unpack(destination: Path) -> int:
    root = Path(__file__).resolve().parent
    encoded = ''.join(''.join((root/'parts'/f'{i:02d}.b64').read_text(encoding='ascii').split()) for i in range(5))
    payload = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(payload).hexdigest() != EXPECTED:
        raise ValueError('CAPSULE_SHA256_MISMATCH')
    if destination.exists():
        raise FileExistsError('Destination already exists; retained evidence is never overwritten')
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:xz') as archive:
        members = archive.getmembers()
        if len(members) != 114 or sum(m.size for m in members) > 2_000_000:
            raise ValueError('CAPSULE_SIZE_MISMATCH')
        names = [m.name for m in members]
        if len(set(names)) != len(names):
            raise ValueError('DUPLICATE_MEMBER')
        for member in members:
            name = PurePosixPath(member.name)
            if not member.isfile() or name.is_absolute() or '..' in name.parts or '\\' in member.name:
                raise ValueError('UNSAFE_MEMBER')
        contents = {m.name: archive.extractfile(m).read() for m in members}
    manifest = json.loads(contents['CONTENTS.json'])
    if set(contents) != set(manifest) | {'CONTENTS.json'}:
        raise ValueError('MANIFEST_FILE_SET_MISMATCH')
    for name, expected in manifest.items():
        raw = contents[name]
        if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
            raise ValueError('MEMBER_DIGEST_MISMATCH: ' + name)
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in contents.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(raw)
    return len(contents)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps({'verified_files': unpack(args.destination), 'destination': str(args.destination)}))
