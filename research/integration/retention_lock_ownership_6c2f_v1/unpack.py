"""Restore hash-bound research evidence only; never import or run a study."""
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination already exists')
    manifest = json.loads((source / 'CAPSULE.json').read_text(), object_pairs_hook=unique)
    if manifest['format'] != 'utf8-file-map-xz-v1':
        raise ValueError('unsupported format')
    for key, limit in [('archive_bytes', 1048576), ('expanded_bytes', 16777216), ('files', 2000)]:
        if type(manifest[key]) is not int or not 0 < manifest[key] <= limit:
            raise ValueError('invalid bound: ' + key)
    if type(manifest['parts']) is not list or not 1 <= len(manifest['parts']) <= 128:
        raise ValueError('invalid parts')
    chunks = []
    for index, part in enumerate(manifest['parts']):
        if part['path'] != f'parts/evidence.{index:02d}':
            raise ValueError('noncanonical part order/path')
        if type(part['bytes']) is not int or not 0 < part['bytes'] <= 65536:
            raise ValueError('invalid part bound')
        path = source / part['path']
        if path.is_symlink() or path.stat().st_size != part['bytes']:
            raise ValueError('part type/size mismatch')
        data = path.read_bytes()
        if digest(data) != part['sha256']:
            raise ValueError('part digest mismatch')
        obj = b'blob ' + str(len(data)).encode() + b'\0' + data
        if hashlib.sha1(obj).hexdigest() != part['git_blob']:
            raise ValueError('part Git object mismatch')
        chunks.append(data)
    archive = b''.join(chunks)
    if len(archive) != manifest['archive_bytes'] or digest(archive) != manifest['archive_sha256']:
        raise ValueError('archive mismatch')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=134217728)
    expanded = decoder.decompress(archive, max_length=manifest['expanded_bytes'] + 1)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('incomplete or trailing archive')
    if len(expanded) != manifest['expanded_bytes'] or digest(expanded) != manifest['expanded_sha256']:
        raise ValueError('expanded mismatch')
    files = json.loads(expanded, object_pairs_hook=unique)
    if type(files) is not dict or len(files) != manifest['files']:
        raise ValueError('file count mismatch')
    encoded = {}
    for name, content in files.items():
        if type(name) is not str or type(content) is not str:
            raise ValueError('non-text entry')
        path = PurePosixPath(name)
        if (not name or '\\' in name or '\0' in name or path.is_absolute()
                or any(p in ('', '.', '..') for p in name.split('/'))):
            raise ValueError('unsafe entry path')
        encoded[name] = content.encode('utf-8')
    for name in encoded:
        if any(str(parent) in encoded for parent in PurePosixPath(name).parents):
            raise ValueError('file/directory collision')
    # Input is fully validated before creating the fresh private destination.
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in encoded.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as output:
            output.write(data)
    return {'status': 'PASS_RESTORATION', 'files': len(encoded),
            'archive_sha256': digest(archive), 'formal_executions': 0}


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: python unpack.py NEW_DIRECTORY')
        print(json.dumps(restore(Path(__file__).resolve().parent, sys.argv[1]), sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, lzma.LZMAError) as exc:
        print('REFUSED: ' + str(exc), file=sys.stderr)
        sys.exit(2)
