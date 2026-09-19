"""Check archived real decisions survive schema parsing without byte changes."""
import hashlib,json
from pathlib import Path
from native_mcp_v1 import NativeDecision
from native_exchange_v1 import encoded
root=Path(__file__).resolve().parent
rows=[]
for path in sorted((root/'requests').glob('*.json')):
    raw=path.read_bytes()
    parsed=NativeDecision.model_validate_json(raw)
    assert encoded(parsed.model_dump(mode='json',exclude_unset=True))==raw,path
    rows.append({'path':path.name,'sha256':hashlib.sha256(raw).hexdigest()})
assert len(rows)==6
print(json.dumps({'status':'PASS_SCOPED','requests':rows,
 'defaults_inserted':False,'new_gui_run':False,'model_utility':'unmeasured'},indent=2))
