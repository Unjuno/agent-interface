"""Restore a verified research capsule for offline audit; never execute an experiment."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(manifest_name):
    manifest = json.loads((HERE/manifest_name).read_text())
    parts = []
    for name, expected in sorted(manifest['parts'].items()):
        data = (HERE/name).read_bytes()
        if sha(data) != expected['sha256']:
            raise ValueError('PART_HASH_MISMATCH:'+name)
        parts.append(data.strip())
    packed = base64.b64decode(b''.join(parts), validate=True)
    if sha(packed) != manifest['bundle_sha256']:
        raise ValueError('BUNDLE_HASH_MISMATCH')
    return gzip.decompress(packed), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raw, manifest = unpack('SOURCE_MANIFEST.json')
    files = json.loads(raw)
    if set(files) != set(manifest['files']):
        raise ValueError('FILE_SET_MISMATCH')
    for name, text in files.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or sha(text.encode()) != manifest['files'][name]:
            raise ValueError('INVALID_FILE:'+name)
    args.out.mkdir(parents=True, exist_ok=False)
    for name, text in files.items():
        target = args.out/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode())
    # Every restored capsule is historical; the single formal allocation must not replay.
    (args.out/'CONSUMED').write_text('Restored historical allocation; offline audit only.\n')
    if (HERE/'EVIDENCE_MANIFEST.json').exists():
        raw, evidence = unpack('EVIDENCE_MANIFEST.json')
        if sha(raw) != evidence['raw_sha256']:
            raise ValueError('RAW_HASH_MISMATCH')
        (args.out/'raw.jsonl').write_bytes(raw)
        for name in ('execution.json', 'audit_result.json', 'validation.json'):
            data = (HERE/name).read_bytes()
            if sha(data) != evidence['files'][name]:
                raise ValueError('RESULT_FILE_HASH_MISMATCH:'+name)
            (args.out/name).write_bytes(data)
    print(json.dumps({'restored_files':len(files), 'output':str(args.out), 'experiment_executed':False}))


if __name__ == '__main__':
    main()
