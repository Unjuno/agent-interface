from pathlib import Path
import json
import sys
import time
from runtime.host_v1.file_publication import publish_json

case=Path('/var/tmp/agent-interface-evidence-storage-main/runtime/results/primary-exchange-live-01/case')
request=json.loads(Path(sys.argv[1]).read_text())
name=f"{request['id']:03}.json"
publish_json(case/'commands'/name,request)
deadline=time.monotonic()+60
while not (case/'replies'/name).exists():
    if (case/'host-exception.json').exists():raise RuntimeError((case/'host-exception.json').read_text())
    if time.monotonic()>deadline:raise TimeoutError('same request remains allocated: wait; do not resend')
    time.sleep(.02)
reply=json.loads((case/'replies'/name).read_text())
value=json.loads(Path(reply['original_reply_path']).read_text())
text=value.get('result',{}).get('content',[]) if isinstance(value,dict) else []
meta=json.loads(next((b['text'] for b in text if b['type']=='text'),'{}'))
selected={k:meta[k] for k in ('status','source','source_sequence','alias','minted','feedback','image_status','image_reference') if k in meta}
if isinstance(meta.get('result'),dict):
    selected['input_status']=meta['result'].get('status')
    selected['releases']=meta['result'].get('execution',{}).get('releases')
print(json.dumps({'id':reply['id'],'attempt':reply['attempt'],'metadata':selected,
    'images':reply['images'],'caller_state':reply['caller_state'],'isError':value.get('result',{}).get('isError') if isinstance(value,dict) else None},indent=2))
