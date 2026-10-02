import json,sys,time
from pathlib import Path
case=Path(sys.argv[1]);wanted=int(sys.argv[2]);end=time.monotonic()+3
while True:
    found=None
    for line in (case/'primary-stream.jsonl').read_bytes().splitlines(keepends=True):
        if not line.endswith(b'\n'):continue
        row=json.loads(line)
        if row.get('result',{}).get('id')==wanted or row.get('status') in ('command_error','terminal'):found=row
    if found:
        result=found.get('result',{})
        reply=json.loads(Path(result['original_reply_path']).read_text()) if result.get('original_reply_path') else None
        meta=None
        if isinstance(reply,dict):
            for item in reply.get('result',{}).get('content',[]):
                if item.get('type')=='text':
                    try:meta=json.loads(item['text'])
                    except ValueError:meta=item['text']
                    break
        selected={k:v for k,v in result.items() if k!='presented_text'}
        if isinstance(meta,dict) and not meta.get('error'):
            meta={k:v for k,v in meta.items() if k in ('status','monotonic_ns','binding_revision','session','error','review_request','expires_at_ns','evidence','capture_consistency','image_status','outcome_summary','post_dispatch_inspection','release','release_attempted','connection_close_attempted') or k=='result'}
            if isinstance(reply,dict):
                full=json.loads(next(b['text'] for b in reply['result']['content'] if b['type']=='text'))
                meta['receipt_execution_summary']=full.get('receipt',{}).get('execution_summary')
        print(json.dumps({'stream_status':found['status'],'result':selected,'selected_original_metadata':meta},indent=2));break
    if time.monotonic()>end:
        print(json.dumps({'status':'observation_timeout','resend_allowed':False,'wait_same_handle':True}));break
    time.sleep(.05)

