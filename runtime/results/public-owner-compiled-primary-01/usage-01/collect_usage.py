import json,base64,hashlib
from pathlib import Path
from usage_projection import project
out=Path(__file__).resolve().parent
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
start='call_e25WKbKck88SpXtpp7eQ37FC';end=None;lines=[];records=[];images=[];context=None;active=False
with source.open() as f:
 for index,line in enumerate(f,1):
  row=json.loads(line);p=row.get('payload',{});kind=p.get('type')
  if row.get('type')=='turn_context':context=(index,line)
  if kind=='custom_tool_call' and p['call_id']==start:active=True
  if not active:lines.append('{}\n');continue
  if not records and context:
   n,c=context
   if n<index:lines[n-1]=c;records.append({'source_line':n,'raw_line':c})
  lines.append(line)
  if row.get('type') in ('turn_context','token_usage_record') or kind in ('custom_tool_call','custom_tool_call_output'):records.append({'source_line':index,'raw_line':line})
  if kind=='custom_tool_call' and end is None and 'PUBLIC_OWNER_COMPILED_DIAGNOSIS_BOUNDARY_01' in p.get('input',''):end=p['call_id']
  if kind=='custom_tool_call_output' and isinstance(p.get('output'),list):
   for block in p['output']:
    url=block.get('image_url','')
    if block.get('type')=='input_image' and ';base64,' in url:
     header,data=url.split(';base64,',1);binary=base64.b64decode(data);images.append({'source_line':index,'sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'media_type':header[5:],'detail':block.get('detail')})
  if kind=='custom_tool_call_output' and p.get('call_id')==end:break
if not active or end is None:raise ValueError('missing boundary')
selection=[{'name':'public-owner-api-development-two-failures-and-diagnosis','begin_call_id':start,'end_call_id':end}]
result=project(lines,selection)
expected=[json.loads((out.parent/c/'replies'/f'{i:03d}.json').read_text())['reply']['image_reference']['sha256'] for c,i in [('normal-compiled',1),('short-compiled',1),('short-compiled',3)]]+['39487881f46367b76654b39d71009ff5cb9a17ba2ad7eabe742d57cbc3117780']
if sorted(expected)!=sorted(x['sha256'] for x in images):raise ValueError(('image multiset',expected,images))
for name,data in [('usage-selection.json',selection),('primary-usage.json',result),('primary-images.json',{'images':images,'expected_sha256':expected,'exact_multiset_matches':True})]:
 (out/name).write_text(json.dumps(data,indent=2)+'\n')
(out/'primary-source-records.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in records))
print(json.dumps({'records':len(records),'images':len(images),'windows':[{'status':w['status'],'totals':w['totals'],'calls':len(w['calls']),'usage_records':len(w['usage_records'])} for w in result['windows']]}))
