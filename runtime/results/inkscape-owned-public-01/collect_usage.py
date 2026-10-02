"""Read-only actual primary usage through fixed terminal-audit boundary."""
import json,hashlib,base64,re
from pathlib import Path
from research.live_control.primary_usage_projection import project
out=Path(__file__).resolve().parent
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
lines=[];records=[];images=[];context=None;begin=None;end=None;owner_begin=None;owner_end=None
with source.open() as f:
 for index,line in enumerate(f,1):
    row=json.loads(line);p=row.get('payload',{});kind=p.get('type');s=p.get('input','')
    if row.get('type')=='turn_context':context=(index,line)
    if kind=='custom_tool_call':
        if begin is None and "'integration/inkscape-owned-public-20261002','github/main'" in s:begin=p['call_id']
        if owner_begin is None and '$inkOwner' in s and 'owner.py' in s:owner_begin=p['call_id']
        if owner_begin is not None and 'tools.write_stdin' in s and re.search(r'session_id\s*:\s*23417\b',s):owner_end=p['call_id']
        if end is None and 'INKSCAPE_OWNED_PUBLIC_TERMINAL_AUDIT_20261002' in s:end=p['call_id']
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
                header,data=url.split(';base64,',1);binary=base64.b64decode(data)
                images.append({'source_line':index,'sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'media_type':header[5:],'detail':block.get('detail')})
    if kind=='custom_tool_call_output' and p.get('call_id')==end:break
if None in (begin,end,owner_begin,owner_end):raise ValueError(('incomplete boundaries',begin,end,owner_begin,owner_end))
selections=[{'name':'preparation-through-terminal-audit','begin_call_id':begin,'end_call_id':end},{'name':'allocation-setup-through-owner-terminal','begin_call_id':owner_begin,'end_call_id':owner_end}]
windows=[project(lines,[s])['windows'][0] for s in selections]
expected=[json.loads((out/'fresh-01/replies'/f'{i:03d}.json').read_text())['reply']['image_reference']['sha256'] for i in (1,2,3)]
if sorted(expected)!=sorted(i['sha256'] for i in images):raise ValueError('primary image blocks do not match exact selected reply PNGs')
result={'schema':'primary-usage-projection-v2','windows':windows,'scope':'whole-context responses; windows overlap, never sum them','billing':'unavailable; no price inferred','excluded':'planning before branch creation and publication after terminal audit, not zero'}
(out/'usage-selection.json').write_text(json.dumps(selections,indent=2)+'\n')
(out/'primary-usage.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'primary-images.json').write_text(json.dumps({'images':images,'exact_reply_image_multiset_matches':True},indent=2)+'\n')
(out/'primary-source-records.jsonl').write_text(''.join(json.dumps(rec)+'\n' for rec in records))
print(json.dumps({'windows':[{'name':w['name'],'status':w['status'],'totals':w['totals']} for w in windows],'records':len(records),'images':len(images)}))
