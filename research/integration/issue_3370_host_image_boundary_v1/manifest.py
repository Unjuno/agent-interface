"""Create a deterministic SHA-256 inventory of retained experiment evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = []
for path in sorted((HERE/'evidence').rglob('*')):
    if not path.is_file() or path.name == 'manifest.json' or '__pycache__' in path.parts:
        continue
    data = path.read_bytes()
    rows.append({'path': path.relative_to(HERE).as_posix(),
                 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
manifest = {'schema': 'agent-interface/issue-3370-evidence-manifest-v1',
            'evidence_root': 'evidence/', 'files': rows}
(HERE/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
print(json.dumps({'file_count': len(rows),
                  'manifest_sha256': hashlib.sha256((HERE/'manifest.json').read_bytes()).hexdigest()},
                 sort_keys=True))
