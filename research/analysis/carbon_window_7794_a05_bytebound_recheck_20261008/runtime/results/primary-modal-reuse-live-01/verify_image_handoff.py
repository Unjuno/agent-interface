from pathlib import Path
import base64
import hashlib
import json

root=Path(__file__).resolve().parent
images=[]
def inspect(value,index,path=''):
    if isinstance(value,dict):
        for key,item in value.items():
            data=None
            if isinstance(item,str) and item.startswith('data:image/') and ';base64,' in item:
                data=base64.b64decode(item.split(';base64,',1)[1],validate=True)
            elif key=='data' and isinstance(item,str) and value.get('type')=='image':
                data=base64.b64decode(item,validate=True)
            if data is not None:
                images.append({'source_line':index,'json_path':path+'/'+key,'bytes':len(data),
                    'sha256':hashlib.sha256(data).hexdigest(),'detail':value.get('detail')})
            elif isinstance(item,(dict,list)):inspect(item,index,path+'/'+key)
    elif isinstance(value,list):
        for offset,item in enumerate(value):inspect(item,index,path+'/'+str(offset))
for line in (root/'actual-source-records.jsonl').read_text().splitlines():
    wrapper=json.loads(line);inspect(json.loads(wrapper['raw_line']),wrapper['source_line'])
if len(images)!=8:raise ValueError('actual tool image count differs')
for image,(arm,index) in zip(images,[("full",i) for i in (1,5,7,9,11)]+[("reuse",i) for i in (1,5,11)]):
    data=(root/arm/'exchange'/f'image-{index}-1.png').read_bytes()
    if image['bytes']!=len(data) or image['sha256']!=hashlib.sha256(data).hexdigest() or image['detail']!='original':
        raise ValueError('native/file/tool image handoff differs')
print(json.dumps({'status':'PASS_ENCODED_TOOL_IMAGE_IDENTITY','images':images,
    'scope':'Encoded tool output only; provider preprocessing/model perception not independently attested'},indent=2))
