"""One read of retained primary output. No sensor, polling, action or authority."""
import json,sys
from pathlib import Path
case=Path(sys.argv[1]);wanted=int(sys.argv[2]);rows=[]
for line in (case/'primary-stream.jsonl').read_bytes().splitlines(keepends=True):
    if line.endswith(b'\n'):rows.append(json.loads(line))
matches=[r for r in rows if r.get('result',{}).get('id')==wanted]
if not matches:
    print(json.dumps({'status':'command_not_yet_observed','resend_allowed':False,'wait_same_handle':True,
      'last_status':rows[-1].get('status') if rows else None}));sys.exit(0)
if len(matches)!=1:raise ValueError('ambiguous command record')
row=matches[0];result=row['result'];reply=json.loads(Path(result['original_reply_path']).read_text())
meta=None
if isinstance(reply,dict):
    for item in reply.get('result',{}).get('content',[]):
        if item.get('type')=='text':
            meta=json.loads(item['text']);break
selected={k:v for k,v in result.items() if k!='presented_text'}
notices=[x for x in result.get('presented_text',[]) if isinstance(x,dict)]
if isinstance(meta,dict) and not meta.get('error'):
    keep=('status','monotonic_ns','binding_revision','session','error','review_request','expires_at_ns','evidence',
      'capture_consistency','image_status','outcome_summary','post_dispatch_inspection','release','release_attempted','connection_close_attempted','result')
    full=meta;meta={k:v for k,v in full.items() if k in keep}
    meta['receipt_execution_summary']=full.get('receipt',{}).get('execution_summary')
print(json.dumps({'stream_status':row['status'],'result':selected,
 'presentation_notices':notices,'selected_original_metadata':meta},indent=2))