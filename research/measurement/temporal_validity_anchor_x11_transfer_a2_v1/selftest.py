import json,tempfile
from pathlib import Path
from aggregate import validate_rows
# Pure harness-only controls. No X11/formal rows.
def row(i):
 order=['SOURCE_APPLIED','CURRENT_EVIDENCE'] if i%2==0 else ['CURRENT_EVIDENCE','SOURCE_APPLIED']
 return {'pair':i,'delay_ms':([130,145,160]*8)[i],'arms':[{'anchor':x} for x in order]}
rows=[row(i) for i in range(24)]
validate_rows(rows)
controls=[]
def reject(name,mut):
 x=json.loads(json.dumps(rows));mut(x)
 ok=False
 try:validate_rows(x)
 except RuntimeError:ok=True
 controls.append({'name':name,'rejected':ok})
reject('pair_order',lambda x:x[0].__setitem__('pair',1))
reject('delay',lambda x:x[3].__setitem__('delay_ms',999))
reject('arm_order',lambda x:x[2].__setitem__('arms',list(reversed(x[2]['arms']))))
assert all(c['rejected'] for c in controls)
print(json.dumps({'valid_schedule':True,'controls':controls},indent=2))
