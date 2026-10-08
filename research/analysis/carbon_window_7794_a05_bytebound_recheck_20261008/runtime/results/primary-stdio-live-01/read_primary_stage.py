from pathlib import Path
import json
import sys
import time

root=Path('/var/tmp/agent-interface-evidence-storage-main/runtime/results/primary-stdio-live-01/case')
command=int(sys.argv[1]);deadline=time.monotonic()+3
while True:
    raw=(root/'primary-stream.jsonl').read_text()
    complete=raw.rsplit('\n',1)[0].splitlines() if '\n' in raw else []
    rows=[json.loads(line) for line in complete]
    matches=[r for r in rows if r.get('status')=='returned' and r.get('result',{}).get('id')==command]
    if len(matches)>1:raise ValueError('duplicate completed command')
    if matches:break
    errors=[r for r in rows if r.get('status') in ('command_error','terminal')]
    if errors:raise RuntimeError(json.dumps(errors[-1]))
    if time.monotonic()>deadline:raise TimeoutError('same command still pending; never send it again')
    time.sleep(.02)
row=matches[0];result=row['result']
metas=[json.loads(value) for value in result['presented_text'] if isinstance(value,str)]
meta=metas[0] if metas else {}
source=meta.get('source',{})
selected={key:meta[key] for key in ('status','operation','image_status','alias','offset','source_sequence','lifetime','release','release_attempted','connection_close_attempted','task_success','authority_granted') if key in meta}
if source:selected['source']={key:source[key] for key in ('sequence','capture_ns','binding_revision','pointer_binding') if key in source}
if isinstance(meta.get('feedback'),dict):
    selected['feedback']={key:meta['feedback'][key] for key in ('status','expected_title','rejected_titles','title','after_title','task_success','authority_granted','input_dispatched') if key in meta['feedback']}
if isinstance(meta.get('result'),dict):
    selected['input_status']=meta['result'].get('status')
    selected['releases']=meta['result'].get('execution',{}).get('releases')
print(json.dumps({'id':command,'attempt':result['attempt'],'metadata':selected,'images':result['images'],
    'caller_state':result['caller_state'],'mcp_status':[v for v in result['presented_text'] if isinstance(v,dict)],
    'projection':'Selected original metadata only; full response/raw stdout retained','original_reply_path':result['original_reply_path']},indent=2))
