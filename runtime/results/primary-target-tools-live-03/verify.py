import base64,hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent;case=root/'case'
def require(ok,message):
    if not ok:raise ValueError(message)
def read(path):return json.loads(path.read_text())
rows=[json.loads(line) for line in (case/'primary-stream.jsonl').read_text().splitlines()]
require([r['status'] for r in rows]==['ready']+['returned']*7+['terminal'],'seven sequential commands and terminal')
for i,row in enumerate(rows[1:-1],1):
    require(row['result']==read(case/'exchange'/f'presentation-{i}.json'),'exact original presentation')
request=read(case/'exchange'/'request-5.json')
require(request['args'][1].get('review') is True,'original caller argument error retained')
reply=read(case/'exchange'/'original-reply-5.json')
meta=json.loads(next(b['text'] for b in reply['result']['content'] if b['type']=='text'))
require(reply['result']['isError'] is True and meta.get('unknown_arguments')==['review'],'actual schema refusal')
require(meta.get('operation_invoked') is False and meta.get('input_dispatched') is False,'refusal before input')
require(rows[5]['result']['caller_state']['stopped']=='unexpected MCP refusal','sticky original STOP')
require(rows[5]['result']['images']==[],'no manufactured input image')
require(not (case/'exchange'/'image-5-1.png').exists(),'failed view did not create image')
close=read(case/'exchange'/'original-reply-7.json')
cm=json.loads(next(b['text'] for b in close['result']['content'] if b['type']=='text'))
require(cm['status']=='closed' and cm['release_attempted'] is False and cm['connection_close_attempted'] is True,'connection-only explicit close after no input')
require(rows[-1]['exit']=={'code':0,'signal':None},'transport exit')
require(read(case/'cleanup.json')['host_exit']==0,'owner host terminal')
require(read(case/'evaluation.json')['actual_nonempty_cells']=={} and read(case/'evaluation.json')['success'] is False,'independent blank workbook')
image=rows[1]['result']['images'][0];raw=Path(image['path']).read_bytes()
require(hashlib.sha256(raw).hexdigest()==image['sha256'],'original initial file identity')
initial=read(case/'exchange'/'original-reply-1.json')
block=next(b for b in initial['result']['content'] if b['type']=='image')
require(raw==base64.b64decode(block['data']),'initial returned PNG unchanged')
require(read(case/'host'/'review-1.json')['relay_id']==1 and read(case/'host'/'review-1.json')['images'][0]['sha256']==image['sha256'],'explicit original image review')
require(len(list((case/'host').glob('request-*.json')))==4,'observe clock refused input close')
require(len(list((case/'calls').glob('*/request.json')))==2,'only actual observe and close admitted by public server')
require(read(root/'manifest.json')['sha256']==hashlib.sha256((root/'runtime.pyz').read_bytes()).hexdigest(),'archive identity')
print(json.dumps({'status':'PASS_FAILURE_RETENTION','task_success':False,'public_relay_attempts':4,'admitted_server_requests':2,'primary_commands':7,'delivered_images':1,'task_input_programs':0,'scope':'retained caller failure and original image/file identity; no modal selection or efficiency success'},indent=2))

