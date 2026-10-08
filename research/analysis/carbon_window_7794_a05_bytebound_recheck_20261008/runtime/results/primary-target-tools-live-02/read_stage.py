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
        print(json.dumps({'stream_status':found['status'],'result':result,'original_metadata':meta},indent=2));break
    if time.monotonic()>end:
        print(json.dumps({'status':'observation_timeout','resend_allowed':False,'wait_same_handle':True}));break
    time.sleep(.05)
