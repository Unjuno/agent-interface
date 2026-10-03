"""Prepare distinct public event-reference cases before the v2 comparison."""
import hashlib,json,time
from pathlib import Path
p=Path(__file__).resolve().parent; parent=p.parent
original=json.loads((parent/'fixtures.json').read_bytes())[:97]
event={'event':'terminal','status':'cancelled','release':{'verified':True,'keys_down':[],'buttons_down':[]},'detail':'critical'}
def change(value):
 if type(value) is dict:
  if value=={'observation_ref':'/native_result/observation'}: return {'event_ref':0}
  return {k:change(v) for k,v in value.items()}
 if type(value) is list:return [change(x) for x in value]
 return value
cases=[]
for row in original:
 path=row['view']['observation_references'][0].replace('/native_result/','/report/',1)
 cases.append({'id':row['id'],'view':{'schema':'agent-interface/receipt-view-v2-event-refs','event_references':{path:0},'reference_scope':'test','events':[event],'report':{'rows':change(row['view']['native_result']['rows'])}}})
cases.append({'id':'97','view':{'schema':'agent-interface/receipt-view-v2-event-refs','event_references':{'/report':0},'reference_scope':'test','events':[event],'report':{'event_ref':0}}})
with (p/'fixtures.json').open('x') as f: json.dump(cases,f,ensure_ascii=False,indent=2);f.write('\n')
source=Path('runtime/cli_v1/receipt_references.py'); test=Path('runtime/cli_v1/test_native_reference_pointer.py')
(p/'PLAN.json').write_text(json.dumps({'kind':'ordinary engineering comparison, not formal','prepared_utc_ns':time.time_ns(),'decision':'All event references must match the independent JSON pointer oracle; malformed paths must raise ValueError; native v1/v2 194 rows must remain correct; inputs unchanged.','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256((p/'fixtures.json').read_bytes()).hexdigest()},indent=2)+'\n')
