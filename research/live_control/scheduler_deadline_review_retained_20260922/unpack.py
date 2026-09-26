#!/usr/bin/env python3
"""Restore retained data only; never imports or executes archived study code."""
import base64
import gzip
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys

PREFIX = 'research/live_control/scheduler_deadline_review_3934_v1/'

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def expand_runs(runs, expected):
    require(type(runs) is list, 'run list')
    result = []
    for pair in runs:
        require(type(pair) is list and len(pair) == 2, 'run pair')
        count, value = pair
        require(type(count) is int and 0 < count <= 300 and type(value) is int, 'run types')
        require(len(result) + count <= expected, 'run extent')
        result.extend([value] * count)
    require(len(result) == expected, 'run denominator')
    return result

def restore_tables(value):
    if type(value) is dict:
        if set(value) == {'__lossless_table_v1__'}:
            spec = value['__lossless_table_v1__']
            require(type(spec) is list and len(spec) == 5, 'table shape')
            count, first, due_runs, delay_runs, residual_runs = spec
            require(type(count) is int and 10 < count <= 300 and type(first) is int, 'table count')
            increments = expand_runs(due_runs, count - 1)
            delays = expand_runs(delay_runs, count)
            residuals = expand_runs(residual_runs, count)
            result = []
            for i in range(count):
                if i:
                    first += increments[i - 1]
                result.append([first, first + delays[i], delays[i] + residuals[i]])
            return result
        return {key: restore_tables(item) for key, item in value.items()}
    if type(value) is list:
        return [restore_tables(item) for item in value]
    return value

def restore(source, destination):
    source = Path(source).resolve()
    destination = Path(destination)
    require(not destination.exists() and not destination.is_symlink(), 'destination must be new')
    manifest = json.loads((source / 'CAPSULE.json').read_text())
    require(manifest['format'] == 'review-retention-v1', 'format')
    require(manifest['files'] == 168 and manifest['file_bytes'] == 4692380, 'manifest denominator')
    require(len(manifest['parts']) == 8, 'part count')
    chunks = []
    for i, part in enumerate(manifest['parts']):
        require(part['name'] == f'capsule-{i:02d}.b64', 'part order')
        encoded = (source / part['name']).read_bytes()
        require(len(encoded) <= 7000, 'encoded part size')
        data = base64.b64decode(encoded.strip(), validate=True)
        require(len(data) == part['bytes'] and digest(data) == part['sha256'], 'part digest')
        chunks.append(data)
    capsule = b''.join(chunks)
    require(len(capsule) == manifest['capsule_bytes'] == 39964, 'capsule size')
    require(digest(capsule) == manifest['capsule_sha256'], 'capsule digest')
    decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
    expanded = decoder.decompress(capsule, max_length=3000001)
    require(decoder.eof and not decoder.unused_data, 'compressed framing')
    require(len(expanded) == manifest['expanded_bytes'] and len(expanded) <= 3000000, 'expanded size')
    require(digest(expanded) == manifest['expanded_sha256'], 'expanded digest')
    payload = json.loads(expanded)
    require(payload['format'] == manifest['format'], 'payload format')
    files = payload['files']
    require(type(files) is dict and len(files) == 168, 'file count')
    decoded = {}
    total = 0
    for name, record in files.items():
        relative = PurePosixPath(name)
        require(name.startswith(PREFIX) and not relative.is_absolute() and '..' not in relative.parts, 'path')
        codec = record['codec']
        if codec == 'json-tables':
            style = record['style']
            require(set(style) <= {'sort_keys', 'separators', 'indent'}, 'JSON style')
            require(record['newline'] in ('', '\n'), 'newline')
            data = (json.dumps(restore_tables(record['value']), **style) + record['newline']).encode()
        elif codec == 'utf8':
            data = record['text'].encode()
        elif codec == 'base64':
            data = base64.b64decode(record['text'], validate=True)
        else:
            raise ValueError('codec')
        if record.get('gzip') is True:
            data = gzip.compress(data, compresslevel=9, mtime=0)
        require(len(data) == record['size'] and digest(data) == record['sha256'], 'file digest: ' + name)
        total += len(data)
        require(total <= 4692380, 'file-byte limit')
        decoded[name] = data
    require(total == 4692380, 'file-byte denominator')
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in decoded.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    return {'files': len(decoded), 'bytes': total, 'all_original_file_hashes_match': True,
            'executes_study_code': False, 'destination': str(destination.resolve())}

if __name__ == '__main__':
    try:
        require(len(sys.argv) == 2, 'usage: unpack.py NEW_DESTINATION')
        print(json.dumps(restore(Path(__file__).parent, sys.argv[1]), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError) as error:
        print(json.dumps({'status': 'STOP_RESTORE', 'detail': str(error)}), file=sys.stderr)
        sys.exit(1)
