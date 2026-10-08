"""Restore retained data only. Never imports or runs experimental sources."""
import base64
import hashlib
import json
import lzma
import sys
from pathlib import Path, PurePosixPath


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def check(ok, message):
    if not ok:
        raise ValueError(message)


def restore(destination):
    source = Path(__file__).resolve().parent
    meta_bytes = (source / 'PACK.json').read_bytes()
    check(len(meta_bytes) < 20000, 'oversized manifest')
    meta = json.loads(meta_bytes, object_pairs_hook=unique)
    check(meta['file_count'] == 82 and len(meta['files']) == 82, 'file count')
    check(meta['compressed_bytes'] == 22040 and meta['uncompressed_bytes'] == 394945, 'bounds')
    check(len(meta['parts']) == 4, 'part count')
    chunks = []
    for i, item in enumerate(meta['parts'], 1):
        check(item['path'] == f'evidence.part{i}.b64', 'part name')
        raw = (source / item['path']).read_bytes()
        check(len(raw) <= 7501 and len(raw) == item['bytes'], 'part bytes')
        check(digest(raw) == item['sha256'], 'part digest')
        chunks.append(b''.join(raw.split()))
    compressed = base64.b64decode(b''.join(chunks), validate=True)
    check(len(compressed) == 22040, 'compressed bytes')
    check(digest(compressed) == meta['compressed_sha256'], 'compressed digest')
    dec = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
    expanded = dec.decompress(compressed, max_length=394946)
    check(dec.eof and not dec.unused_data and len(expanded) == 394945, 'expanded bounds')
    check(digest(expanded) == meta['uncompressed_sha256'], 'expanded digest')
    files = json.loads(expanded, object_pairs_hook=unique)
    check(type(files) is dict and set(files) == set(meta['files']), 'inventory')
    prepared = {}
    for name, text in files.items():
        check(type(name) is str and type(text) is str, 'member type')
        q = PurePosixPath(name)
        check(not q.is_absolute() and '\\' not in name and ':' not in name,
              'unsafe path')
        check(q.as_posix() == name and all(v not in ('', '.', '..') for v in q.parts),
              'noncanonical path')
        content = text.encode('utf-8')
        item = meta['files'][name]
        check(len(content) == item['bytes'] and digest(content) == item['sha256'],
              'member hash or size')
        prepared[name] = content
    out = Path(destination)
    check(out.is_absolute() and not out.is_symlink() and not out.exists(), 'fresh absolute output required')
    for parent in out.parents:
        check(not parent.is_symlink(), 'symlink ancestor')
    check(out.parent.is_dir(), 'parent directory must exist')
    out.mkdir(mode=0o700)
    for name, content in prepared.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(content)
    return {'files': len(prepared), 'bytes': sum(map(len, prepared.values())),
            'formal_PASS': False, 'executed_experiment': False}


if __name__ == '__main__':
    try:
        check(len(sys.argv) == 2, 'usage: unpack.py /absolute/new/directory')
        print(json.dumps(restore(sys.argv[1]), sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, lzma.LZMAError) as exc:
        print(f'RESTORE_REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
