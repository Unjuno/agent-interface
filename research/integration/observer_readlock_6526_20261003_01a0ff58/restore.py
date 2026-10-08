"""Restore newly constructed native witnesses into a fresh private archive copy."""
import base64
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    entries = json.loads((root / 'custody/manifest.json').read_bytes())['files']
    for entry in entries:
        name = entry['name']
        if name != Path(name).name or '/' in name or '\\' in name:
            raise ValueError('native witness name escapes directory')
        target = root / 'custody/native' / name
        if target.exists():
            raise FileExistsError('restore only into a fresh private copy: ' + name)
    for entry in entries:
        name = entry['name']
        data = base64.b64decode((root / 'custody/native' / (name + '.b64')).read_bytes().strip(), validate=True)
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('native capsule differs: ' + name)
        with (root / 'custody/native' / name).open('xb') as stream:
            stream.write(data)
    print(json.dumps({'decoded_native_witnesses': len(entries), 'producer_run': False}))


if __name__ == '__main__':
    main()
