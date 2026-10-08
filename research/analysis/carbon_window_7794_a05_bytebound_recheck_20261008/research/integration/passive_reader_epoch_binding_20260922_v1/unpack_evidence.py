"""Verify and unpack retained evidence; does not execute experiment sources."""
import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'evidence/MANIFEST.json').read_bytes())
    encoded = []
    for part in manifest['parts']:
        data = (ROOT / part['path']).read_bytes()
        if len(data) != part['bytes'] or sha(data) != part['sha256']:
            raise ValueError('evidence part mismatch: ' + part['path'])
        encoded.append(data.strip())
    packed = base64.b64decode(b''.join(encoded), validate=True)
    if sha(packed) != manifest['xz_sha256']:
        raise ValueError('xz mismatch')
    payload = lzma.decompress(packed, memlimit=128 * 1024 * 1024)
    if len(payload) != manifest['payload_bytes'] or sha(payload) != manifest['payload_sha256']:
        raise ValueError('payload mismatch')
    archive = json.loads(payload)
    if archive['schema'] != 'epoch-evidence-bundle-v1' or len(archive['files']) != manifest['member_count']:
        raise ValueError('bundle schema/count mismatch')
    for name, content in archive['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or not path.parts or type(content) is not str:
            raise ValueError('invalid member: ' + name)
    args.destination.mkdir(parents=True, exist_ok=False)
    for name, content in archive['files'].items():
        path = args.destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as output:
            output.write(content.encode('utf-8'))
    print(json.dumps({'status': 'VERIFIED_UNPACK', 'members': len(archive['files']),
                      'payload_sha256': sha(payload), 'destination': str(args.destination)}, sort_keys=True))


if __name__ == '__main__':
    main()
