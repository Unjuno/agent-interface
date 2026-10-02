"""Read-only primary usage accounting through the retained terminal audit."""
import json,re,subprocess,hashlib,base64
from pathlib import Path
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
lines=[];records=[];images=[];lastctx=None;begin=None;end=None;starts={};ends={}
handles={52312:'fresh-01-wait-100',14713:'fresh-01-region'}
with source.open() as f:
 for index,line in enumerate(f,1):
  row=json.loads(line);p=row.get('payload',{});kind=p.get('type');s=p.get('input','')
  if row.get('type')=='turn_context':lastctx=(index,line)
  if kind=='custom_tool_call':
   if begin is None and "['git','checkout','-b','integration/direct-selected-image-20261002'" in s:begin=p['call_id']
   m=re.search(r'owner\.py .*?/(fresh-01-(?:wait-100|region)) (1002[45]01) compact (100)',s)
   if m:
    name=m.group(1)
    if name in starts:raise ValueError('Duplicate owner launch')
    starts[name]=p['call_id']
   for handle,name in handles.items():
    if re.search(r'session_id\s*:\s*'+str(handle)+r'\b',s) and 'tools.write_stdin' in s:
     if name in ends:raise ValueError('Duplicate owner terminal handle')
     ends[name]=p['call_id']
   if 'REGION_ADMISSION_TERMINAL_AUDIT_20261002' in s and end is None:end=p['call_id']
  if begin is None:lines.append('{}\n');continue
  if not records and lastctx:
   n,c=lastctx
   if n<index:lines[n-1]=c;records.append({'source_line':n,'raw_line':c})
  lines.append(line)
  if row.get('type') in ('turn_context','token_usage_record') or kind in ('custom_tool_call','custom_tool_call_output'):records.append({'source_line':index,'raw_line':line})
  if kind=='custom_tool_call_output' and isinstance(p.get('output'),list):
   for block in p['output']:
    url=block.get('image_url','')
    if block.get('type')=='input_image' and url.startswith('data:') and ';base64,' in url:
     header,data=url.split(';base64,',1);binary=base64.b64decode(data)
     images.append({'source_line':index,'sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'media_type':header[5:],'detail':block.get('detail')})
  if kind=='custom_tool_call_output' and p.get('call_id')==end:break
if begin is None or end is None or len(starts)!=2 or starts.keys()!=ends.keys():raise ValueError(('Incomplete source boundaries',begin,end,starts,ends))
selection=[{'name':'joint-direct-and-region-admission-through-terminal-audit','begin_call_id':begin,'end_call_id':end}]+[{'name':n,'begin_call_id':starts[n],'end_call_id':ends[n]} for n in sorted(starts)]
ns={'__name__':'projection_import'};exec(compile(subprocess.check_output(['git','show','67ebd3016af9ed99a5cb40a39d4d753871f51d75:research/live_control/primary_usage_projection.py'],cwd=root,text=True),'projection','exec'),ns)
joint=ns['project'](lines,selection[:1]);owners=ns['project'](lines,selection[1:])
result={'windows':joint['windows']+owners['windows'],'scope':'Joint overlaps owner projections; projected separately and must never be summed.'}
(out/'usage-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
(out/'primary-usage.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'primary-images.json').write_text(json.dumps({'images':images},indent=2)+'\n')
(out/'primary-source-records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
print(json.dumps({'windows':[{'name':w['name'],'status':w['status'],'totals':w['totals'],'begin':w['begin'],'end':w['end']} for w in result['windows']],'records':len(records),'image_blocks':len(images),'scope':'Joint and owner views overlap; never add together. Host/image ingestion/billing not measured. Excludes planning before the first branch creation and later publication, not zero.'}))
