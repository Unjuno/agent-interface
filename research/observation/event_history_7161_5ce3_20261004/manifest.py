import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='FILES.json' and '__pycache__' not in p.parts)
with (ROOT/'FILES.json').open('x') as f:json.dump({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},f,indent=2);f.write('\n')
print(len(paths))
