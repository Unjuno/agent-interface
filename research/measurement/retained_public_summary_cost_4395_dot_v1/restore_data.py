"""Restore exact retained bytes to a NEW directory; never import or run study code."""
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('invalid logical path')
    p = PurePosixPath(name)
    if p.is_absolute() or str(p) != name or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('unsafe logical path')
    return name


def check(data, record):
    if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('byte/hash mismatch')
    git = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if git != record['git_blob_sha1']:
        raise ValueError('Git blob mismatch')


def restore(package, destination):
    manifest = json.loads((package / 'TRANSPORT_MANIFEST.json').read_bytes())
    records = manifest['files']
    if len(records) != 56 or manifest['logical_file_count'] != 56:
        raise ValueError('unexpected logical count')
    for name, record in records.items():
        safe_name(name)
        if record['location'] != name or record['storage'] not in ('direct', 'zip_member'):
            raise ValueError('unsupported mapping')
    archive = manifest['archive']
    encoded = (package / safe_name(archive['path'])).read_bytes()
    if len(encoded) != archive['encoded_bytes'] or hashlib.sha256(encoded).hexdigest() != archive['encoded_sha256']:
        raise ValueError('encoded archive mismatch')
    if not encoded.endswith(b'\n'):
        raise ValueError('missing transport newline')
    decoded = base64.b64decode(encoded[:-1], validate=True)
    if len(decoded) != archive['decoded_bytes'] or hashlib.sha256(decoded).hexdigest() != archive['decoded_sha256']:
        raise ValueError('decoded archive mismatch')
    outputs = {}
    expected = {n for n, r in records.items() if r['storage'] == 'zip_member'}
    with zipfile.ZipFile(io.BytesIO(decoded)) as z:
        infos = z.infolist()
        if len(infos) != len(expected) or len(infos) != archive['members'] or {i.filename for i in infos} != expected:
            raise ValueError('unexpected/duplicate archive members')
        for info in infos:
            name = safe_name(info.filename)
            if info.is_dir() or not stat.S_ISREG(info.external_attr >> 16) or info.file_size != records[name]['bytes']:
                raise ValueError('unexpected member type/size')
            outputs[name] = z.read(info)
    for name, record in records.items():
        if record['storage'] == 'direct':
            source = package / name
            if source.is_symlink() or not source.is_file():
                raise ValueError('direct source is not a regular file')
            outputs[name] = source.read_bytes()
        check(outputs[name], record)
    if sum(map(len, outputs.values())) != manifest['logical_byte_count']:
        raise ValueError('total byte count mismatch')
    # All input bytes validate BEFORE destination creation. Existing targets fail.
    destination.mkdir(exist_ok=False)
    for name, data in sorted(outputs.items()):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(data)
    return {'restored_files': len(outputs), 'restored_bytes': sum(map(len, outputs.values())), 'scientific_invocations': 0}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B restore_data.py NEW_EMPTY_DESTINATION')
    print(json.dumps(restore(Path(__file__).resolve().parent, Path(sys.argv[1])), sort_keys=True))
