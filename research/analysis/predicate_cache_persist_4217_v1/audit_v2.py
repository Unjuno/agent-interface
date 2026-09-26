import json,pathlib,sys
from audit import audit_data
R=pathlib.Path(__file__).parent; d=json.loads((R/'FORMAL_V2.json').read_text()); s=audit_data(d)
(R/'AUDIT_V2.json').write_text(json.dumps(s,sort_keys=True,indent=2)+'\n'); print(json.dumps(s,sort_keys=True)); sys.exit(0 if s['pass_contract'] else 1)
