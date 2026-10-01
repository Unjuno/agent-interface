"""Restore retained bytes only. Never execute experiment code or infer results.

The two original JSONL streams are losslessly column-encoded saved records.
The redundant first-delivery ZIP is rebuilt from its retained bytes/ZIP metadata;
its SHA-256 must match (DEFLATE9 compatible with zlib 1.3.1 is required).
Publication inputs and destination parent must be trusted and quiescent.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

MAX_ARCHIVE = 1_000_000
MAX_TAR = 16_000_000
MAX_FILES = 200

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safe_name(name: str) -> str:
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('invalid member name')
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '.' in p.parts or str(p) != name:
        raise ValueError('noncanonical member name')
    return name

def decode_tar(raw: bytes, count: int) -> dict[str, bytes]:
    if len(raw) > MAX_TAR:
        raise ValueError('tar limit')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as tf:
        members = tf.getmembers()
        if len(members) != count or len(members) > MAX_FILES:
            raise ValueError('member count')
        total = 0
        for m in members:
            name = safe_name(m.name)
            if not m.isfile() or name in result or m.size < 0:
                raise ValueError('nonregular or duplicate member')
            total += m.size
            if total > MAX_TAR:
                raise ValueError('member limit')
            f = tf.extractfile(m)
            if f is None:
                raise ValueError('missing member bytes')
            value = f.read(m.size + 1)
            if len(value) != m.size:
                raise ValueError('member length')
            result[name] = value
    return result

def decode_rows(data: bytes) -> tuple[bytes, bytes]:
    doc = json.loads(data)
    count = doc['rows']
    if type(count) is not int or not 0 < count <= 10_000:
        raise ValueError('row count')
    columns = {}
    for path, values in doc['columns']:
        if not isinstance(path, list) or len(path) > 16 or any(type(x) not in (str, int) for x in path):
            raise ValueError('column path')
        key = tuple(path)
        if key in columns or len(values) != count:
            raise ValueError('duplicate column or length')
        columns[key] = values
    if len(columns) > 100:
        raise ValueError('column limit')
    def rebuild(path: tuple, row: int):
        node = columns[path][row]
        if not isinstance(node, list) or len(node) != 2:
            raise ValueError('missing column value')
        tag, value = node
        if tag == 'D':
            if not isinstance(value, list) or any(type(k) is not str for k in value) or len(set(value)) != len(value):
                raise ValueError('dictionary keys')
            return {k: rebuild(path + (k,), row) for k in value}
        if tag == 'L':
            if type(value) is not int or not 0 <= value <= 100:
                raise ValueError('list length')
            return [rebuild(path + (k,), row) for k in range(value)]
        if tag == 'V' and not isinstance(value, (dict, list)):
            return value
        raise ValueError('column tag')
    records = [rebuild((), i) for i in range(count)]
    def lines(values):
        return ''.join(json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n' for x in values).encode()
    raw = lines(records)
    inputs = lines({'id': r['id'], 'input': r['input']} for r in records)
    return inputs, raw

def restore(publication: Path, destination: Path) -> dict:
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination exists')
    meta = json.loads((publication / 'CAPSULE.json').read_text())
    if meta['format'] != 'c6t9-lossless-v1' or not 0 < meta['archive_bytes'] <= MAX_ARCHIVE:
        raise ValueError('capsule format or size')
    chunks = []
    seen = set()
    for spec in meta['parts']:
        name = safe_name(spec['path'])
        if name in seen:
            raise ValueError('duplicate part')
        seen.add(name)
        part = publication / name
        if part.is_symlink() or not part.is_file() or part.stat().st_size != spec['bytes']:
            raise ValueError('part missing or size')
        b = part.read_bytes()
        if digest(b) != spec['sha256']:
            raise ValueError('part hash')
        chunks.append(b)
    archive = b''.join(chunks)
    if len(archive) != meta['archive_bytes'] or digest(archive) != meta['archive_sha256']:
        raise ValueError('archive identity')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(archive, max_length=MAX_TAR + 1)
    if len(raw) > MAX_TAR or not decoder.eof or decoder.unused_data:
        raise ValueError('decompression bound or trailing stream')
    if len(raw) != meta['tar_bytes'] or digest(raw) != meta['tar_sha256']:
        raise ValueError('tar identity')
    files = decode_tar(raw, meta['tar_members'])
    files['INPUTS.jsonl'], files['run01/raw.jsonl'] = decode_rows(files['_packing/rows.json'])
    manifest = json.loads(files['_packing/original_manifest.json'])
    recipe = json.loads(files['_packing/zip.json'])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.comment = base64.b64decode(recipe['comment'], validate=True)
        for entry in recipe['members']:
            name = safe_name(entry['name'])
            source = safe_name(entry['source'])
            attrs = entry['attributes']
            zi = zipfile.ZipInfo(name, tuple(attrs['date_time']))
            allowed = {'compress_type','create_system','create_version','extract_version','reserved','flag_bits','volume','internal_attr','external_attr'}
            for key in allowed:
                setattr(zi, key, attrs[key])
            for key in ('comment', 'extra'):
                setattr(zi, key, base64.b64decode(attrs[key], validate=True))
            z.writestr(zi, files[source], compresslevel=9)
    files[safe_name(recipe['name'])] = buf.getvalue()
    if len(manifest) != meta['original_members'] or len(manifest) > MAX_FILES:
        raise ValueError('original count')
    total = 0
    for name, spec in manifest.items():
        safe_name(name)
        b = files[name]
        total += len(b)
        if len(b) != spec['bytes'] or digest(b) != spec['sha256']:
            raise ValueError('original identity: ' + name)
    if total != meta['original_bytes']:
        raise ValueError('original byte count')
    # All data are verified before writing anything. No tar extraction or code execution.
    destination.mkdir(parents=True, exist_ok=False)
    for name in manifest:
        p = destination / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(files[name])
    return {'restored_files': len(manifest), 'restored_bytes': total,
            'archive_sha256': meta['archive_sha256'], 'scientific_runs': 0}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).resolve().parent, args.destination), sort_keys=True, indent=2))
