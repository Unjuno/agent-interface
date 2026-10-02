import json,hashlib,base64
from pathlib import Path
from usage_projection import project
out=Path(__file__).resolve().parent
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
lines=[];records=[];images=[];context=None;begin=None;end=None;methods={}
names=[x['case'] for x in json.loads((out/'schedule.json').read_text())]
with source.open() as f:
 for index,line in enumerate(f,1):
  row=json.loads(line);p=row.get('payload',{});kind=p.get('type');s=p.get('input','')
  if row.get('type')=='turn_context':context=(index,line)
  if kind=='custom_tool_call':
   if begin is None and "print(name,i,a['sha256'],rat)" in s:begin=p['call_id']
   if begin is not None:
    for name in names:
     if "('"+name+"',4,'method')" in s:
      if name in methods:raise ValueError('duplicate method')
      methods[name]=p['call_id']
    if end is None and "'retained',len(files),'files; all4owners terminal'" in s:end=p['call_id']
  if begin is None:lines.append('{}\n');continue
  if not records and context:
   n,c=context
   if n<index:lines[n-1]=c;records.append({'source_line':n,'raw_line':c})
  lines.append(line)
  if row.get('type') in ('turn_context','token_usage_record') or kind in ('custom_tool_call','custom_tool_call_output'):records.append({'source_line':index,'raw_line':line})
  if kind=='custom_tool_call_output' and isinstance(p.get('output'),list):
   for block in p['output']:
    url=block.get('image_url','')
    if block.get('type')=='input_image' and url.startswith('data:') and ';base64,' in url:
     header,data=url.split(';base64,',1);binary=base64.b64decode(data);images.append({'source_line':index,'sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'media_type':header[5:],'detail':block.get('detail')})
  if kind=='custom_tool_call_output' and p.get('call_id')==end:break
if begin is None or end is None or set(methods)!=set(names):raise ValueError(('incomplete selection',begin,end,methods))
selections=[{'name':'joint-construction-through-terminal-verifier','begin_call_id':begin,'end_call_id':end}]+[{'name':n+'-bounded-method-image-response','begin_call_id':methods[n],'end_call_id':methods[n]} for n in names]
windows=[project(lines,[s])['windows'][0] for s in selections]
expected=[json.loads((out/n/'replies'/f'{i:03d}.json').read_text())['reply']['image_reference']['sha256'] for n in names for i in (1,4)]
if sorted(expected)!=sorted(x['sha256'] for x in images):raise ValueError(('image multiset',expected,images))
(out/'usage-selection.json').write_text(json.dumps(selections,indent=2)+'\n')
(out/'primary-usage.json').write_text(json.dumps({'windows':windows,'billing':'unavailable','scope':'Joint includes construction, development checks, all4cases and terminal verification through selected final tool response. Method windows are nested response-only windows for issuing full bounded select/move/check/Save and presenting final original image; exclude initial grounding, reference mints, subsequent primary semantic review/close and construction. Never sum nested levels; not whole-task cost or per-tool attribution.','confounds':'fixed order, evolving context/cache, application readiness/pixels; no causal route savings or immutable model attestation','excluded':'Earlier turns and current accounting/publication after the selected end; not zero cost.','prior_failures':'Preserved separately; normal compiled failed in single-method01, interior successor is a new fixed condition, not replacement.'},indent=2)+'\n')
(out/'primary-images.json').write_text(json.dumps({'images':images,'exact_reply_image_multiset_matches':True},indent=2)+'\n')
(out/'primary-source-records.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in records))
print(json.dumps({'records':len(records),'images':len(images),'windows':[{'name':w['name'],'status':w['status'],'totals':w['totals']} for w in windows]}))
