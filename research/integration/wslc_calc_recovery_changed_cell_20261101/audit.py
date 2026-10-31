from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics,xml.etree.ElementTree as ET,csv
from PIL import Image,ImageOps
from io import BytesIO,StringIO
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

p=Path(__file__).with_name('public.zip');H=lambda b:hashlib.sha256(b).hexdigest();assert H(p.read_bytes())=='e9ad4f6610e5dc7b9edea94d2750c9ca4d9a2bab929e5b962afafbe9f5c0c261'
with ZipFile(p) as z:
 m=read(z,'manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 v=read(z,'verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 def screenshot(tag,native):
  a=native['native']['artifact'];blob=z.read(tag+'/output/'+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'];return Image.open(BytesIO(blob)).convert('RGB')
 results=[];sessions=set()
 for tag in ('n01','n02'):
  c=read(z,tag+'/conditions.json');assert c['allocation']==tag and c['calls_max']==2
  for n,h in c['candidate'].items():assert H(z.read(tag+'/candidate/'+n))==h
  assert H(z.read(tag+'/candidate/launcher.py'))==c['launcher_sha256'] and H(z.read('source-hashes.json'))==c['source_manifest_sha256']
  launch=read(z,tag+'/launcher-result.json');assert launch['container_exit']==1 and launch['host_exit']==0 and not launch['live_handle_unresolved']
  method=read(z,tag+'/output/method/result.json')['method_receipt'];assert method['outcome']=='SAFE_YIELD' and method['reason']=='effect_unavailable' and method['completed_transitions']==1 and method['transitions'][0]['action']=='enter' and method['transitions'][0]['release_verified']
  ex=[n for n in z.namelist() if n.startswith(tag+'/output/owner/') and n.endswith('-execution.json')];assert len(ex)==1;entry=read(z,ex[0]);assert entry['request']['action']=='enter' and entry['result']['status']=='completed' and release(entry['result'])
  prior=read(z,tag+'/output/prior-close.json');final=read(z,tag+'/output/final-neutral.json');assert prior['release']['verified'] and not prior['release']['keys_down'] and not prior['release']['buttons_down'] and final['close']['status']=='closed' and not final['keys_down'] and not final['buttons'];assert z.read(tag+'/output/finally-saved.fods')==z.read(tag+'/candidate/blank.fods') and vals(z.read(tag+'/output/finally-saved.fods'))==[]
  actor=read(z,tag+'/output/interference.json')
  if tag=='n01':
   assert actor['status']=='refused' and actor['input_dispatched'] is False and not actor['additional_input_checks'][0]['eligible'] and final['close']['release']['verified'] and tag+'/output/interference-record.json' not in z.namelist() and not any(n.startswith(tag+'/output/recovery-owner/') for n in z.namelist())
   obs=[]
   for i in (1,2):
    names=[n for n in z.namelist() if n.startswith(tag+'/output/interference-owner/') and n.endswith('/observation-'+str(i)+'.json')];assert len(names)==1;obs.append(read(z,names[0]))
   assert obs[0]['pointer_binding']==obs[1]['pointer_binding'] and screenshot(tag,obs[0]).crop((350,20,370,35)).tobytes()!=screenshot(tag,obs[1]).crop((350,20,370,35)).tobytes();outcome='actor refused before input'
  else:
   record=read(z,tag+'/output/interference-record.json');assert actor['status']=='completed' and actor['recovery_required'] is False and release(actor) and record['close']['release']['verified'] and not record['close']['release']['keys_down'] and not record['close']['release']['buttons_down'] and len({prior['session_id'],record['session_id'],final['close']['session_id']})==3
   programs=[read(z,n) for n in z.namelist() if n.startswith(tag+'/output/interference-owner/') and '/program-' in n and n.endswith('.json')];assert len(programs)==1;ops=programs[0]['ops'];assert ''.join(x.get('text','') for x in ops if x.get('op')=='text')=='999' and any(x.get('keys')==['CTRL','Home'] for x in ops) and any(x.get('keys')==['Return'] for x in ops)
   after=screenshot(tag,record['after']);crop=after.crop((95,144,126,159)).convert('L').resize((124,60),Image.Resampling.LANCZOS);crop=ImageOps.expand(crop,border=16,fill=255);assert crop.tobytes()==Image.open(BytesIO(z.read(tag+'/output/interference-a1.png'))).convert('L').tobytes() and record['ocr_returncode']==0
   words=[x for x in csv.DictReader(StringIO(z.read(tag+'/output/interference-a1.tsv').decode()),delimiter='\t') if x.get('text','').strip()];assert len(words)==1 and words[0]['text']=='999' and float(words[0]['conf'])>=90
   rec=read(z,tag+'/output/reobservations.json');assert len(rec)>0 and all(x['filled'] is False for x in rec);reference=Image.open(BytesIO(z.read(tag+'/candidate/reference.png'))).convert('RGB');boxes=[(100,145,123,157),(100,162,123,174)]
   for row in rec:
    names=[n for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and n.endswith('/observation-'+str(row['sequence'])+'.json')];assert len(names)==1;im=screenshot(tag,read(z,names[0]));assert any(im.crop(b).tobytes()!=reference.crop(b).tobytes() for b in boxes)
   assert not any(n.startswith(tag+'/output/recovery-owner/') and ('/mint-' in n or '/program-' in n) for n in z.namelist()) and tag+'/output/recovery-save.json' not in z.namelist();outcome='actor input completed; OCR 999; recovery refused'
  calls=[];session=None
  for i in (1,2):
   req=read(z,f'{tag}/exchange/request-{i}.json');resp=read(z,f'{tag}/exchange/response-{i}.json');raw=read(z,f'{tag}/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and H(z.read(f'{tag}/exchange/image-{i}.png'))==req['image_sha256']==resp['image_sha256'] and raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed';session=session or raw['thread_id'];assert raw['thread_id']==session;calls.append(raw['usage'])
  assert session not in sessions;sessions.add(session);results.append({'allocation':tag,'result':outcome,'saved_values':[],'final_neutral':True,'usage':{k:sum(x[k] for x in calls) for k in ['input_tokens','cached_input_tokens','output_tokens']}})
 print(json.dumps({'status':'audited','results':results},indent=2))
