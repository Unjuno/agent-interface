"""Data-only, bounded restoration; never executes the stored study."""
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate manifest member')
        obj[key] = value
    return obj

def decode(root=ROOT):
    manifest = json.loads((root/'CAPSULE.json').read_text(), object_pairs_hook=unique)
    if manifest['capsule_bytes'] > 1000000 or manifest['decompressed_json_bytes'] > 1000000:
        raise ValueError('capsule exceeds restoration bound')
    chunks = []
    for part in manifest['parts']:
        name = part['name']
        if PurePosixPath(name).name != name or '\\' in name:
            raise ValueError('invalid part path')
        data = (root/name).read_bytes()
        if len(data) != part['bytes'] or sha(data) != part['sha256']:
            raise ValueError('part identity mismatch')
        chunks.append(data)
    encoded = b''.join(chunks)
    if len(encoded) != manifest['capsule_bytes'] or sha(encoded) != manifest['capsule_sha256']:
        raise ValueError('capsule identity mismatch')
    decoder = lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw = decoder.decompress(encoded, max_length=manifest['decompressed_json_bytes']+1)
    if not decoder.eof or decoder.unused_data or len(raw) != manifest['decompressed_json_bytes']:
        raise ValueError('invalid expanded envelope')
    members = json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
    if type(members) is not dict or len(members) != manifest['member_count']:
        raise ValueError('member count mismatch')
    for name, text in members.items():
        path = PurePosixPath(name)
        if (not isinstance(text, str) or path.is_absolute() or '..' in path.parts
                or str(path) != name or not path.parts or '\\' in name):
            raise ValueError('noncanonical member')
    if sum(len(text.encode('utf-8')) for text in members.values()) != manifest['member_bytes']:
        raise ValueError('expanded byte count mismatch')
    return members

def restore(destination, root=ROOT):
    members = decode(root)
    destination = Path(destination)
    destination.mkdir(exist_ok=False)
    for name, text in members.items():
        target = destination/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode('utf-8'))
    return len(members)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: unpack.py NEW_DIRECTORY')
    print(json.dumps({'restored_files': restore(sys.argv[1])}))
