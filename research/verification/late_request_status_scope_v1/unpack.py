"""Bounded, data-only restoration. Never imports or executes archived source."""
import argparse
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile


def checked_map(root):
    meta = json.loads((root / 'ARCHIVE.json').read_text())
    if not 0 < meta['xz_bytes'] <= 200000 or not 0 < meta['tar_bytes'] <= 16000000:
        raise ValueError('archive size bound')
    packed = b''
    names = set()
    for part in meta['parts']:
        name = part['name']
        if Path(name).name != name or name in names:
            raise ValueError('part name')
        names.add(name)
        data = (root / name).read_bytes()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError('part integrity')
        packed += base64.b64decode(data.strip(), validate=True)
    if len(packed) != meta['xz_bytes'] or hashlib.sha256(packed).hexdigest() != meta['xz_sha256']:
        raise ValueError('packed integrity')
    dec = lzma.LZMADecompressor(memlimit=134217728)
    raw = dec.decompress(packed, max_length=16000001)
    if not dec.eof or dec.unused_data or len(raw) != meta['tar_bytes']:
        raise ValueError('decompression bound')
    if hashlib.sha256(raw).hexdigest() != meta['tar_sha256']:
        raise ValueError('tar integrity')
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or str(path) != member.name:
                raise ValueError('unsafe member')
            if member.name in members or len(members) >= 2000:
                raise ValueError('duplicate/excess members')
            if member.size < 0 or sum(len(v) for v in members.values()) + member.size > 12000000:
                raise ValueError('expanded size')
            members[member.name] = archive.extractfile(member).read()
    if len(members) != meta['members'] or sum(map(len, members.values())) != meta['member_bytes']:
        raise ValueError('member denominator')
    manifest = json.loads(members['MEMBERS.json'])
    if set(manifest) != set(members) - {'MEMBERS.json'}:
        raise ValueError('manifest membership')
    for name, expected in manifest.items():
        data = members[name]
        if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise ValueError('member integrity: ' + name)
    return members


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out', type=Path); a = ap.parse_args()
    if a.out.exists(): raise FileExistsError('new destination required')
    members = checked_map(Path(__file__).resolve().parent)
    a.out.mkdir(parents=True, exist_ok=False)
    for name, data in members.items():
        dest = a.out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as f: f.write(data)
    print(json.dumps({'status': 'PASS_DATA_RESTORATION', 'members': len(members),
                      'bytes': sum(map(len, members.values()))}, sort_keys=True))


if __name__ == '__main__':
    main()
