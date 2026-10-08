import json,base64,hashlib
from pathlib import Path
from usage_projection import project
from context_projection import project_context
out=Path(__file__).resolve().parent
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
start=None;end=None;lines=[];records=[];images=[];context=None;active=False
with source.open() as f:
 for index,line in enumerate(f,1):
  row=json.loads(line);p=row.get('payload',{});kind=p.get('type');code=p.get('input','')
  if row.get('type')=='turn_context':context=(index,line)
  if kind=='custom_tool_call' and start is None and 'runtime/results/calc-owner-transfer-live-01/save_guard.py' in code and 'def _emit' in code:
   start=p['call_id'];active=True
  if not active:lines.append('{}\n');continue
  if not records and context:
   n,c=context
   if n<index:lines[n-1]=c;records.append({'source_line':n,'raw_line':c})
  lines.append(line)
  if row.get('type') in ('turn_context','token_usage_record') or kind in ('custom_tool_call','custom_tool_call_output'):
   records.append({'source_line':index,'raw_line':line})
  if kind=='custom_tool_call' and end is None and 'PUBLIC_INPUT_GUARD_LIVE_AUDIT_FINALIZED_01' in code:end=p['call_id']
  if kind=='custom_tool_call_output' and isinstance(p.get('output'),list):
   for block in p['output']:
    url=block.get('image_url','')
    if block.get('type')=='input_image' and ';base64,' in url:
     header,data=url.split(';base64,',1);binary=base64.b64decode(data);images.append({'source_line':index,'sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'media_type':header[5:],'detail':block.get('detail')})
  if kind=='custom_tool_call_output' and p.get('call_id')==end:break
if not active or end is None:raise ValueError('missing frozen boundary')
selection=[{'name':'input-guard-initial-integration-discovery-through-two-primary-cases-and-audit','begin_call_id':start,'end_call_id':end}]
result=project(lines,selection)
expected=[]
for case in json.loads((out.parent/'schedule.json').read_text()):
 for path in sorted((out.parent/case['case']/'replies').glob('*.json')):
  value=json.loads(path.read_text()).get('image')
  if value:expected.append(value['sha256'])
if sorted(expected)!=sorted(x['sha256'] for x in images):raise ValueError(('original image multiset differs',len(expected),len(images)))
for name,data in [('usage-selection.json',selection),('primary-usage.json',result),('primary-images.json',{'images':images,'expected_sha256':expected,'exact_multiset_matches':True})]:
 (out/name).write_text(json.dumps(data,indent=2)+'\n')
for record in records:
 if json.loads(record['raw_line']).get('type')=='turn_context':
  record['original_raw_sha256']=hashlib.sha256(record['raw_line'].encode()).hexdigest()
  record['raw_line']=project_context(record['raw_line'])
  record['privacy_projection']={'kind':'turn_context_metadata','payload_fields':['turn_id','model','effort']}
(out/'primary-source-records.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in records))
print(json.dumps({'records':len(records),'images':len(images),'windows':[{'status':w['status'],'totals':w['totals'],'calls':len(w['calls']),'usage_records':len(w['usage_records'])} for w in result['windows']]}))
