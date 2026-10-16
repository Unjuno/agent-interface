import json
from common import run_session
r=run_session(0)
print(json.dumps(r,indent=2,sort_keys=True))
raise SystemExit(0 if r['pass'] else 2)
