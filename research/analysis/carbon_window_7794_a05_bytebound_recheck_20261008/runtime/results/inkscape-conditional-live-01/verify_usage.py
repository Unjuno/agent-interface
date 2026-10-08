import json,hashlib,base64
from pathlib import Path
from research.live_control.primary_usage_projection import project
out=Path(__file__).resolve().parent
records=[json.loads(x) for x in (out/'primary-source-records.jsonl').read_text().splitlines()]
lines=['{}\n']*max(x['source_line'] for x in records)
images=[]
for rec in records:
 lines[rec['source_line']-1]=rec['raw_line'];row=json.loads(rec['raw_line']);p=row.get('payload',{})
 if p.get('type')=='custom_tool_call_output' and isinstance(p.get('output'),list):
  for block in p['output']:
   url=block.get('image_url','')
   if block.get('type')=='input_image' and ';base64,' in url:images.append(hashlib.sha256(base64.b64decode(url.split(';base64,',1)[1])).hexdigest())
actual=[project(lines,[s])['windows'][0] for s in json.loads((out/'usage-selection.json').read_text())]
if actual!=json.loads((out/'primary-usage.json').read_text())['windows']:raise ValueError('usage reconstruction differs')
expected=[x['sha256'] for x in json.loads((out/'primary-images.json').read_text())['images']]
if sorted(expected)!=sorted(images):raise ValueError('original image multiset differs')
print(json.dumps({'status':'PASS','records':len(records),'images':len(images),'windows':len(actual),'scope':'original chronological whole-context usage, not provider-attested isolated cost'}))
