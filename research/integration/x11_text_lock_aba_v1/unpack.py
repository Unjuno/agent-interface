"""Restore retained evidence only; never import or execute restored code."""
import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import re

HERE = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj

def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid bounded integer')
    return value

def load_members(source):
    manifest_bytes = (source / 'CAPSULE.json').read_bytes()
    if len(manifest_bytes) > 32768:
        raise ValueError('manifest bound')
    m = json.loads(manifest_bytes, object_pairs_hook=unique)
    if m['schema'] != 'retained-capsule-v2':
        raise ValueError('manifest schema')
    limit = integer(m['compressed_bytes'], 1, 262144)
    expanded = integer(m['expanded_bytes'], 1, 2097152)
    parts = m['parts']
    if not isinstance(parts, list) or not 1 <= len(parts) <= 64:
        raise ValueError('part count')
    packed = bytearray()
    for index, p in enumerate(parts):
        if p['path'] != f'evidence-{index:02d}.xz.part':
            raise ValueError('part name/order')
        count = integer(p['bytes'], 1, 8192)
        with (source / p['path']).open('rb') as stream:
            data = stream.read(count + 1)
        if len(data) != count or digest(data) != p['sha256']:
            raise ValueError('part identity')
        packed.extend(data)
        if len(packed) > limit:
            raise ValueError('compressed bound')
    if len(packed) != limit or digest(packed) != m['compressed_sha256']:
        raise ValueError('compressed identity')
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    raw = decoder.decompress(packed, max_length=expanded + 1)
    if (not decoder.eof or decoder.unused_data or len(raw) != expanded
            or digest(raw) != m['expanded_sha256']):
        raise ValueError('expanded identity or framing')
    payload = json.loads(raw, object_pairs_hook=unique)
    if payload['schema'] != 'retained-file-map-v2':
        raise ValueError('payload schema')
    members = payload['files']
    if not isinstance(members, list) or len(members) != integer(m['members'], 1, 512):
        raise ValueError('member count')
    decoded = {}
    total = 0
    original_count = 0
    original_bytes = 0
    for row in members:
        name = row['path']
        if (not isinstance(name, str) or not name or len(name) > 240
                or '\\' in name or '\0' in name):
            raise ValueError('member name')
        p = PurePosixPath(name)
        if (p.is_absolute() or any(part in ('', '.', '..') for part in name.split('/'))
                or p.parts[0] not in ('original', 'continuation') or len(p.parts) < 2
                or name in decoded):
            raise ValueError('unsafe or duplicate member')
        if row['encoding'] == 'utf8':
            data = row['content'].encode('utf-8')
        elif row['encoding'] == 'base64':
            data = base64.b64decode(row['content'], validate=True)
        else:
            raise ValueError('member encoding')
        if len(data) != integer(row['bytes'], 0, 262144) or digest(data) != row['sha256']:
            raise ValueError('member identity')
        decoded[name] = data
        total += len(data)
        if total > 2097152:
            raise ValueError('total member bound')
        if p.parts[0] == 'original':
            original_count += 1
            original_bytes += len(data)
    if (total != integer(m['member_bytes'], 0, 2097152)
            or original_count != integer(m['original_files'], 1, 512)
            or original_bytes != integer(m['original_bytes'], 0, 2097152)):
        raise ValueError('original or total denominator')
    for name in decoded:
        if any(str(parent) in decoded for parent in PurePosixPath(name).parents):
            raise ValueError('file/directory collision')
    return decoded

def restore(source, destination):
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination must not exist')
    members = load_members(source)
    destination.mkdir(parents=False, exist_ok=False, mode=0o700)
    for name, data in members.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        target.chmod(0o600)
    return {'status': 'RESTORED_NOT_EXECUTED', 'files': len(members),
            'bytes': sum(map(len, members.values())), 'destination': str(destination)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(HERE, args.destination), sort_keys=True))
