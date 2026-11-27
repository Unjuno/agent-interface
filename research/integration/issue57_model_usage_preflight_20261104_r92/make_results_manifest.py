import hashlib, json
from pathlib import Path
base=Path(__file__).resolve().parent
files=[]
for top in ('r92-a01','mcp-isolation-diagnostic-01','worker-command-diagnostic-01'):
    for p in sorted((base/top).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            files.append({'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,
                          'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(base/'RESULTS-SHA256.json').write_text(json.dumps({'files':files},sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'bytes':sum(f['bytes'] for f in files),'total_sha256':hashlib.sha256((base/'RESULTS-SHA256.json').read_bytes()).hexdigest()}))

