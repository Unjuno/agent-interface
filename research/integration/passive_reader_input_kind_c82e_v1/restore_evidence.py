"""Post-result transfer helper: restore bytes only; never execute the experiment."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
TARGETS = ('formal-01/RAW.json', 'construction-01/RAW.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def restore(destination):
    if destination.exists():
        raise ValueError('DESTINATION_ALREADY_EXISTS')
    manifest = json.loads((ROOT / 'EVIDENCE_MANIFEST.json').read_text())
    validated = {}
    for name in TARGETS:
        entry = manifest[name]
        if not 0 < entry['raw_bytes'] <= 1_000_000:
            raise ValueError('INVALID_RAW_SIZE')
        chunks = []
        for part in entry['parts']:
            relative = Path(part['path'])
            if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'evidence':
                raise ValueError('INVALID_PART_PATH')
            data = (ROOT / relative).read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if len(data) != part['bytes'] or sha(data) != part['sha256'] or blob != part['git_blob']:
                raise ValueError('PART_IDENTITY_MISMATCH:' + part['path'])
            chunks.append(data)
        compressed = b''.join(chunks)
        if len(compressed) != entry['gzip_bytes'] or sha(compressed) != entry['gzip_sha256']:
            raise ValueError('GZIP_IDENTITY_MISMATCH:' + name)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode='rb') as source:
            raw = source.read(entry['raw_bytes'] + 1)
        if len(raw) != entry['raw_bytes'] or sha(raw) != entry['raw_sha256']:
            raise ValueError('RAW_IDENTITY_MISMATCH:' + name)
        validated[name] = raw
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in validated.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as output:
            output.write(data)
    return {name: {'bytes': len(data), 'sha256': sha(data)} for name, data in validated.items()}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python -B restore_evidence.py NEW_OUTPUT_DIRECTORY')
    print(json.dumps(restore(Path(sys.argv[1])), sort_keys=True, indent=2))
