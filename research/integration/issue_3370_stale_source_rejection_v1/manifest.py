"""Hash every retained stale-source experiment input and output."""
import hashlib,json
from pathlib import Path
here=Path(__file__).resolve().parent
rows=[]
for p in sorted((here/'evidence').rglob('*')):
 if p.is_file() and p.name!='manifest.json':
  b=p.read_bytes(); rows.append({'path':p.relative_to(here).as_posix(),'bytes':len(b),
   'sha256':hashlib.sha256(b).hexdigest()})
out={'schema':'agent-interface/issue-3370-stale-source-manifest-v1','files':rows}
(here/'evidence/manifest.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'file_count':len(rows),'sha256':hashlib.sha256((here/'evidence/manifest.json').read_bytes()).hexdigest()}))
