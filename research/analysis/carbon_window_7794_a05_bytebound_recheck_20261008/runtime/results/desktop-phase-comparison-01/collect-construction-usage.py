import json,subprocess,hashlib,base64
from pathlib import Path
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
selection=[dict(name='joint-construction-through-retained-changed-repair-failure-and-correction',begin_call_id='call_wbnOawryjolYrmqByQUrtEEo',end_call_id='call_zrrMpHwVj6geqL0pfTCQ3pU0')]
lines=[];records=[];images=[];lastctx=None
with source.open() as f:
 for index,line in enumerate(f,1):
  if index<171958:
   lines.append('{}\n')
   if '"type":"turn_context"' in line or '"type": "turn_context"' in line:
    if json.loads(line).get('type')=='turn_context':lastctx=(index,line)
   continue
  row=json.loads(line);lines.append(line);payload=row.get('payload',{})
  if row.get('type') in ('turn_context','token_usage_record') or payload.get('type') in ('custom_tool_call','custom_tool_call_output'):records.append(dict(source_line=index,raw_line=line))
  if payload.get('type')=='custom_tool_call_output' and isinstance(payload.get('output'),list):
   for block in payload['output']:
    url=block.get('image_url','')
    if block.get('type')=='input_image' and isinstance(url,str) and url.startswith('data:') and ';base64,' in url:
     head,data=url.split(';base64,',1);binary=base64.b64decode(data)
     images.append(dict(source_line=index,sha256=hashlib.sha256(binary).hexdigest(),bytes=len(binary),media_type=head[5:],detail=block.get('detail')))
  if payload.get('type')=='custom_tool_call_output' and payload.get('call_id')==selection[0]['end_call_id']:break
if lastctx:
 index,line=lastctx;lines[index-1]=line;records.insert(0,dict(source_line=index,raw_line=line))
ns={'__name__':'projection_import'}
exec(compile(subprocess.check_output(['git','show','HEAD:research/live_control/primary_usage_projection.py'],cwd=root,text=True),'projection','exec'),ns)
result=ns['project'](lines,selection)
for name,value in [('construction-usage-selection.json',selection),('construction-primary-usage.json',result),('construction-primary-images.json',dict(images=images))]:(out/name).write_text(json.dumps(value,indent=2)+'\n')
(out/'construction-source-records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
print(json.dumps(dict(totals=result['windows'][0]['totals'],records=len(records),images=images)))
