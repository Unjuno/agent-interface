import json
from common import run_session,evaluate
r=run_session(0);r['errors']=evaluate(r);r['pass']=not r['errors']
print(json.dumps(r,indent=2,sort_keys=True))
raise SystemExit(0 if r['pass'] else 2)
