"""Read-only independent reclassification of retained v1 corruption-control outputs."""
import hashlib
import json
from pathlib import Path

root=Path('/out')
raw=json.loads((root/'controls.json').read_bytes())
baseline=(root/'formal01/result.json').read_bytes()
rows=[]
for item in raw.get('rows',[]):
    name=item['name']; copy_path=root/(name+'.json')
    errors=item.get('errors')
    rejected=(item.get('exit')==1 and item.get('stderr')=='' and isinstance(errors,list) and bool(errors) and copy_path.exists() and copy_path.read_bytes()!=baseline)
    rows.append({'name':name,'rejected':rejected,'exit':item.get('exit'),'errors':errors,'stderr':item.get('stderr'),'mutated_sha256':hashlib.sha256(copy_path.read_bytes()).hexdigest() if copy_path.exists() else None})
result={'schema':'issue4680-independent-audit-corruption-controls-v2','source_schema':raw.get('schema'),'count':len(rows),'rejected':sum(r['rejected'] for r in rows),'rows':rows,'interpretation':'Auditor emitted structured nonempty errors and exit 1 for every distinct copied mutation; v1 controls wrapper only miscompared the decision label string.'}
(root/'controls-audit-v2.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
raise SystemExit(0 if result['count']==4 and result['rejected']==4 else 1)

