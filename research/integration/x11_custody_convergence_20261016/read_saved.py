"""Read-only transport/member verification. No recovered code is imported.

Pins are the hashes published in PR #7148 before this convergence. Successful
verification certifies public bytes, not the omitted originals or native claims.
"""
import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath


PINS = {
    'v4': (156328, '2a6593a455d9af0473eeb5febd80a7fda01c02693b6e22376cbb04bf5502d613',
           4232579, '8986b3cba68e3b9631fb2d03c8358842001b241a3767ba452fca0f6ea39cf5e0', 320, 6),
    'c33c34': (61800, 'af3b56ea10634785ef5ae69e3295146472f7a64b861fa86af1da7f3858629c5b',
              361029, '8b7f3583ce17f7e571d05611e72d23e39854dc5a133f2b8b3ef117557e0fb35b', 71, 16),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_bytes(data, count, digest, label):
    require(len(data) == count and hashlib.sha256(data).hexdigest() == digest,
            'byte/hash mismatch: ' + label)


def safe_member(name):
    require(isinstance(name, str) and bool(name), 'missing member name')
    path = PurePosixPath(name)
    require(not path.is_absolute() and '\\' not in name and ':' not in name
            and all(part not in ('', '.', '..') for part in name.split('/')),
            'unsafe member path: ' + name)
    return path


def regular_file(root, relative):
    path = root
    for part in relative.parts:
        path = path / part
        require(not path.is_symlink(), 'symlink refused: ' + str(relative))
    require(path.is_file(), 'missing member: ' + str(relative))
    return path


def verify(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'regular packet directory required')
    expected = set()
    groups = {}
    for group, (size, digest, json_size, json_digest, members, omitted) in PINS.items():
        path = regular_file(root, PurePosixPath('capsules') / (group + '.xz'))
        require(path.stat().st_size == size, 'capsule length: ' + group)
        packed = path.read_bytes()
        checked_bytes(packed, size, digest, group)
        # Decode only after the exact small compressed object matches its pin.
        raw = lzma.decompress(packed)
        checked_bytes(raw, json_size, json_digest, group + ' JSON')
        doc = json.loads(raw)
        require(len(doc['members']) == members and len(doc['explicit_omissions']) == omitted,
                'capsule inventory: ' + group)
        if group == 'v4':
            require(set(doc['original_manifest']) == set(doc['members']) | set(doc['explicit_omissions']),
                    'original manifest inventory')
        folded = set()
        for name, row in doc['members'].items():
            member = safe_member(name)
            require(name.casefold() not in folded, 'case collision: ' + name)
            folded.add(name.casefold())
            if group == 'v4':
                data = base64.b64decode(row['base64'], validate=True)
                n, h = row['bytes'], row['sha256']
                require(row['original'] == doc['original_manifest'][name], 'original reference: ' + name)
            else:
                data = row['utf8'].encode('utf-8')
                n, h = row['public_bytes'], row['public_sha256']
            checked_bytes(data, n, h, 'capsule member ' + name)
            relative = PurePosixPath('members') / group / member
            file = regular_file(root, relative)
            require(file.stat().st_size == n, 'member length: ' + name)
            checked_bytes(file.read_bytes(), n, h, str(relative))
            expected.add(relative.as_posix())
        groups[group] = dict(public_members=members, explicit_omissions=omitted,
                             compressed_sha256=digest, json_sha256=json_digest)
    actual = set()
    for path in (root / 'members').rglob('*'):
        require(not path.is_symlink(), 'symlink in member inventory')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    require(actual == expected, 'unexpected member inventory')
    capsules = {p.name for p in (root / 'capsules').iterdir()}
    require(capsules == {k + '.xz' for k in PINS}, 'unexpected capsule inventory')
    return dict(status='PUBLIC_BYTES_VERIFIED_ONLY', groups=groups,
                public_members=sum(g['public_members'] for g in groups.values()),
                explicit_omissions=sum(g['explicit_omissions'] for g in groups.values()),
                original_private_bytes_certified=False, native_or_actor_execution=False,
                historical_auditors_replayed=False, adoption='HOLD')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', nargs='?', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(verify(args.packet), indent=2))
