"""Bounded data-only restoration. Does not execute archived scientific code."""
from __future__ import annotations
import argparse, hashlib, io, json, lzma, tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
ARCHIVE_SHA256 = '809078c4a8eda85ef22bd65881a22430cf57ca2aab31795d2f90d71ef981df41'
ARCHIVE_BYTES = 90304
TAR_BYTES = 1464320
MEMBERS = 146
MEMBER_BYTES = 1355239

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def checked_members(raw: bytes) -> dict[str, bytes]:
    if len(raw) != TAR_BYTES:
        raise ValueError('tar length')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as stream:
        for member in stream:
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != member.name or member.name in result
                    or not 0 <= member.size <= MEMBER_BYTES):
                raise ValueError('unsafe or duplicate member')
            handle = stream.extractfile(member)
            if handle is None:
                raise ValueError('missing member data')
            data = handle.read(MEMBER_BYTES + 1)
            if len(data) != member.size:
                raise ValueError('member size')
            result[member.name] = data
            if len(result) > MEMBERS or sum(map(len, result.values())) > MEMBER_BYTES:
                raise ValueError('expansion limit')
    if len(result) != MEMBERS or sum(map(len, result.values())) != MEMBER_BYTES:
        raise ValueError('member totals')
    manifest = json.loads(result['MANIFEST.json'])['files']
    if set(result) != set(manifest) | {'MANIFEST.json'}:
        raise ValueError('original inventory')
    for name, item in manifest.items():
        if len(result[name]) != item['bytes'] or digest(result[name]) != item['sha256']:
            raise ValueError('original member digest: ' + name)
    return result

def restore(out: Path, root: Path = ROOT) -> dict:
    if out.exists() or out.is_symlink():
        raise ValueError('destination exists')
    meta = json.loads((root / 'CAPSULE.json').read_text())
    parts = []
    for i, item in enumerate(meta['parts']):
        if item['path'] != f'capsule/part-{i:03}.bin':
            raise ValueError('part order')
        path = root / item['path']
        if path.is_symlink():
            raise ValueError('part symlink')
        data = path.read_bytes()
        if len(data) != item['bytes'] or digest(data) != item['sha256']:
            raise ValueError('part digest')
        parts.append(data)
    data = b''.join(parts)
    if len(data) != ARCHIVE_BYTES or digest(data) != ARCHIVE_SHA256:
        raise ValueError('archive identity')
    decoder = lzma.LZMADecompressor(memlimit=256 * 1024 * 1024)
    raw = decoder.decompress(data, max_length=TAR_BYTES + 1)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('incomplete or concatenated archive')
    members = checked_members(raw)
    # Caller controls a trusted parent; this is not an adversarial filesystem sandbox.
    out.mkdir(parents=True, exist_ok=False)
    for name, content in members.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(content)
    return {'members': len(members), 'member_bytes': sum(map(len, members.values())),
            'archive_sha256': digest(data)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(args.destination), indent=2, sort_keys=True))
