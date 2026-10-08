"""Freeze prospective source/decision gates and terminal construction receipts once."""
import datetime, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
files = [p for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name != 'FREEZE.json']
record = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'formal_runs': 0, 'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
with (ROOT/'FREEZE.json').open('x') as f: json.dump(record, f, indent=2); f.write('\n')
print(json.dumps({'files': len(files), 'sha256': hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest()}))
