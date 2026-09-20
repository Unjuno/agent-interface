"""Write deterministic hashes for both complete condition evidence trees."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
rows=[]
for path in sorted((HERE/'evidence').rglob('*')):
    if not path.is_file() or path.name=='manifest.json' or '__pycache__' in path.parts:
        continue
    data=path.read_bytes()
    rows.append({'path':path.relative_to(HERE).as_posix(),'bytes':len(data),
                 'sha256':hashlib.sha256(data).hexdigest()})
result={'schema':'agent-interface/issue-3370-delivery-pair-manifest-v1',
        'evidence_root':'evidence/','files':rows}
(HERE/'evidence/manifest.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'file_count':len(rows),'manifest_sha256':hashlib.sha256(
    (HERE/'evidence/manifest.json').read_bytes()).hexdigest()},sort_keys=True))
