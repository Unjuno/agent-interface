#!/usr/bin/env python3
"""Verify/extract retained data without importing or executing experiment code."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath

DIGEST = 'cecb3b5bc63de93d70502c603bba8d5dc6c07233f080e1bcff3f724d959927d8'
ROOTS = ('xterm_property_history_boundary_v1', 'xterm_property_history_atomic_v2')
AUDITS = (
    '6318eefab203948f74357479b63e4751b498ae551b88057848ff3ff393ee2935',
    'ea580e8dd3a0e3c03475e8973f50e13358e374637c05bd91a8c2670c23d8d025',
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='Optional NEW extraction directory')
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    parts = [folder / f'retained.json.xz.part{i:02d}' for i in range(7)]
    require([p.stat().st_size for p in parts] == [6000] * 6 + [32], 'part sizes')
    packed = b''.join(p.read_bytes() for p in parts)
    require(sha(packed) == DIGEST, 'archive SHA-256')
    decoder = lzma.LZMADecompressor(memlimit=256 * 1024 * 1024)
    plain = decoder.decompress(packed, max_length=599677)
    require(decoder.eof and not decoder.unused_data and len(plain) == 599676,
            'archive length or trailing data')
    values = json.loads(plain, object_pairs_hook=unique_pairs)
    require(type(values) is dict and len(values) == 247, 'file cardinality')
    files = {}
    for name, text in values.items():
        path = PurePosixPath(name)
        require(type(text) is str and str(path) == name and len(path.parts) >= 2
                and not path.is_absolute() and path.parts[0] in ROOTS
                and '..' not in path.parts and '\\' not in name, 'file path/type')
        files[name] = text.encode('utf-8')
    summaries = []
    for root, expected, status in zip(ROOTS, AUDITS, ('FAIL', 'PASS')):
        freeze = json.loads(files[root + '/FREEZE.json'])
        for name, expected_source in freeze['sources'].items():
            require(sha(files[root + '/' + name]) == expected_source, 'source: ' + name)
        data = files[root + '/AUDIT.json']
        require(sha(data) == expected, 'retained audit digest')
        audit = json.loads(data)
        require(audit['audit'] == status, 'retained disposition')
        for name, expected_raw in audit['raw_sha256'].items():
            require(sha(files[root + '/formal-01/' + name]) == expected_raw,
                    'raw evidence: ' + name)
        summaries.append({'root': root, 'audit': status, 'totals': audit['totals']})
    if args.out:
        args.out.mkdir(parents=False, exist_ok=False)
        for name, data in files.items():
            target = args.out.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(data)
    print(json.dumps({'archive_sha256': DIGEST, 'files': len(files),
                      'retained': summaries, 'executed_experiments': 0}, indent=2))


if __name__ == '__main__':
    main()
