from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics,xml.etree.ElementTree as ET
from PIL import Image
from io import BytesIO
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
def read(z,p): return json.loads(z.read(p))
def release(row):
    items=row['execution']['releases']
    return bool(items) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in items)
def vals(blob):
    sheets=ET.fromstring(blob).findall('.//'+T+'table'); assert len(sheets)==1
    sheet=sheets[0]; rows=sheet.findall(T+'table-row')
    assert len(rows)==len(sheet.findall('.//'+T+'table-row'))
    populated=[]; row_index=0
    for row in rows:
        repeat=int(row.get(T+'number-rows-repeated','1')); assert repeat>0
        column=0
        for cell in row:
            if cell.tag not in (T+'table-cell',T+'covered-table-cell'): continue
            count=int(cell.get(T+'number-columns-repeated','1')); assert count>0
            kind=cell.get(O+'value-type'); value=cell.get(O+'value'); formula=cell.get(T+'formula'); text=''.join(cell.itertext()).strip()
            if kind is not None or value is not None or formula is not None or text:
                assert repeat==1 and count==1
                populated.append((row_index,column,kind,value,text,formula))
            column+=count
        row_index+=repeat
    return populated

p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='0b0b81bd0a54ae5ff184cae1af3a824152c2ee6883cdf34d54f68f653d26f7d3'
H=lambda b:hashlib.sha256(b).hexdigest()
with ZipFile(p) as z:
 manifest=read(z,'manifest.json');assert set(z.namelist())==set(manifest['files'])|{'manifest.json'}
 for n,h in manifest['files'].items():assert H(z.read(n))==h,n
 verification=read(z,'verification.json');assert verification['source_checked']==2092 and not verification['source_mismatches'] and verification['wslc_list_exit']==0 and verification['running_list_empty']
 rows=[];sessions=set()
 for tag,route,count in [('j01','compiled',2),('j02','fresh',3)]:
  c=read(z,tag+'/conditions.json');assert c['allocation']==tag and c['route']==route and c['calls_max']==count and c['order']==['j01:compiled','j02:fresh'] and c['host_python']=='3.13.14'
  for f,h in c['candidate'].items():assert H(z.read('candidate/'+f))==h
  assert H(z.read('candidate/launcher.py'))==c['launcher_sha256'] and H(z.read('source-hashes.json'))==c['source_manifest_sha256']
  launch=read(z,tag+'/launcher-result.json');assert launch['container_exit']==0 and launch['host_exit']==0 and not launch['live_handle_unresolved']
  r=read(z,tag+'/output/result.json');gate=read(z,tag+'/output/stale-gate.json');assert r['route']==route and gate['sequence']==2 and gate['binding_unchanged'] and not gate['prior_programs_or_mints']
  assert r['saved_score']['pass_effect'] and vals(z.read(tag+'/output/saved.fods'))==[(0,0,'float','731','731',None),(1,0,'float','864','864',None)]
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down'] and not r['buttons']
  names=z.namelist();obs2=[n for n in names if n.startswith(tag+'/output/owner/') and n.endswith('/observation-2.json')];assert len(obs2)==1;stale=read(z,obs2[0]);artifact=stale['native']['artifact'];imagebytes=z.read(tag+'/output/'+artifact['path'].removeprefix('/out/'));assert H(imagebytes)==artifact['sha256'];changed=Image.open(BytesIO(imagebytes)).convert('RGB')
  initial=Image.open(BytesIO(z.read(tag+'/exchange/image-1.png'))).convert('RGB');x,y=gate['first_point'];box=(x-4,y-4,x+4,y+4);assert H(initial.crop(box).tobytes())==gate['before_sha256'] and H(changed.crop(box).tobytes())==gate['after_sha256'] and gate['before_sha256']!=gate['after_sha256']
  mint=[n for n in names if n.startswith(tag+'/output/owner/') and n.endswith('/mint-click_cell.json')];assert len(mint)==1 and read(z,mint[0])['created_sequence']>gate['sequence']
  calls=[];ids=set();thread=None
  for i in range(1,count+1):
   req=read(z,f'{tag}/exchange/request-{i}.json');resp=read(z,f'{tag}/exchange/response-{i}.json');raw=read(z,f'{tag}/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and H(z.read(f'{tag}/exchange/image-{i}.png'))==req['image_sha256']==resp['image_sha256'];assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed' and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low';assert raw['call_id'] not in ids;ids.add(raw['call_id']);calls.append(raw['usage']);thread=thread or raw['thread_id'];assert raw['thread_id']==thread;assert resp.get('close_returned',False)==(i==count);assert 0<=raw['usage']['cached_input_tokens']<=raw['usage']['input_tokens']
  assert read(z,tag+'/exchange/request-1.json')['source_sequence']==1 and read(z,tag+'/exchange/request-2.json')['source_sequence']==3
  obs3=[n for n in names if n.startswith(tag+'/output/owner/') and n.endswith('/observation-3.json')];assert len(obs3)==1;fresh=read(z,obs3[0]);a=fresh['native']['artifact'];assert H(z.read(tag+'/output/'+a['path'].removeprefix('/out/')))==a['sha256']==H(z.read(tag+'/exchange/image-2.png')) and fresh['pointer_binding']==stale['pointer_binding']
  assert thread not in sessions;sessions.add(thread)
  click=read(z,tag+'/output/click-result.json');assert click['status']=='completed' and release(click)
  if route=='fresh':
   assert r['method']['status']=='completed'
   for n in ['fresh-entry.json','fresh-save.json']:
    a=read(z,tag+'/output/'+n);assert a['status']=='completed' and release(a)
  else:
   receipt=r['method']['method_receipt'];assert receipt['outcome']=='TASK_SUCCEEDED' and len(receipt['transitions'])==2 and all(x['release_verified'] for x in receipt['transitions']);assert read(z,tag+'/output/method/saved-effect.json')['verdict']['status']=='succeeded'
  seconds=(r['task_end_ns']-r['task_start_ns'])/1e9;usage={k:sum(u[k] for u in calls) for k in ['input_tokens','cached_input_tokens','output_tokens']};rows.append({'allocation':tag,'route':route,'task_seconds':seconds,'launcher_seconds':launch['elapsed_seconds'],'calls':count,'usage':usage,'saved_effect':True,'neutral':True})
 print(json.dumps({'status':'audited','results':rows},indent=2))
