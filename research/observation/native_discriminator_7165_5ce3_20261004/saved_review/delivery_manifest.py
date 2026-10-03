"""Create closed delivery inventory without modifying original FILES.json."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
target = ROOT/'DELIVERY_FILES.json'
files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p != target and '__pycache__' not in p.parts)
entries = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with target.open('x') as f:
    json.dump(entries, f, indent=2, sort_keys=True)
    f.write('\n')
print(json.dumps({'files': len(entries), 'original_manifest_sha256': entries['FILES.json']}))
