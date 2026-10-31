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

p=Path(__file__).with_name('public.zip');H=lambda b:hashlib.sha256(b).hexdigest();assert H(p.read_bytes())=='9fe08a8c34b333307ef1168ec22f8f4ec7a37590c85542c9b96b61250630060b'
with ZipFile(p) as z:
 m=read(z,'manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 c=read(z,'m01/conditions.json');assert c['allocation']=='m01' and c['route']=='compiled' and c['calls_max']==2
 for n,h in c['candidate'].items():assert H(z.read('candidate/'+n))==h
 assert H(z.read('candidate/launcher.py'))==c['launcher_sha256'] and H(z.read('source-hashes.json'))==c['source_manifest_sha256'];v=read(z,'verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 launch=read(z,'m01/launcher-result.json');assert launch['container_exit']==1 and launch['host_exit']==0 and not launch['live_handle_unresolved'] and 'fresh recovered state unavailable after bounded reobservation' in z.read('m01/container.stderr').decode()
 r=read(z,'m01/output/method/result.json')['method_receipt'];assert r['outcome']=='SAFE_YIELD' and r['reason']=='effect_unavailable' and r['completed_transitions']==1 and len(r['transitions'])==1 and r['transitions'][0]['action']=='enter' and r['transitions'][0]['release_verified'] and r['pending_effect']['effect_ref']==r['transitions'][0]['effect_ref']
 executions=[n for n in z.namelist() if n.startswith('m01/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1;ex=read(z,executions[0]);assert ex['request']['action']=='enter' and ex['result']['status']=='completed' and release(ex['result'])
 prior=read(z,'m01/output/prior-close.json');final=read(z,'m01/output/final-neutral.json');assert prior['status']=='closed' and prior['release']['verified'] and not prior['release']['keys_down'] and not prior['release']['buttons_down'] and final['close']['status']=='closed' and prior['session_id']!=final['close']['session_id'] and not final['keys_down'] and not final['buttons']
 assert not any(n.startswith('m01/output/recovery-owner/') and ('/mint-' in n or '/program-' in n) for n in z.namelist()) and 'm01/output/recovery-save.json' not in z.namelist()
 assert z.read('m01/output/finally-saved.fods')==z.read('candidate/blank.fods') and vals(z.read('m01/output/finally-saved.fods'))==[]
 reference=Image.open(BytesIO(z.read('candidate/reference.png'))).convert('RGB');boxes=[(100,145,123,157),(100,162,123,174)];recorded=read(z,'m01/output/reobservations.json');assert len(recorded)==16 and all(x['filled'] is False for x in recorded)
 captures=[]
 for row in recorded:
  matches=[n for n in z.namelist() if n.startswith('m01/output/recovery-owner/') and n.endswith('/observation-'+str(row['sequence'])+'.json')];assert len(matches)==1;n=read(z,matches[0]);a=n['native']['artifact'];blob=z.read('m01/output/'+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'];image=Image.open(BytesIO(blob)).convert('RGB');assert any(image.crop(b).tobytes()!=reference.crop(b).tobytes() for b in boxes);captures.append(n['capture_ns'])
 assert captures==sorted(captures) and captures[-1]-captures[0]>=2_000_000_000
 calls=[];ids=set();session=None
 for i in (1,2):
  req=read(z,f'm01/exchange/request-{i}.json');resp=read(z,f'm01/exchange/response-{i}.json');raw=read(z,f'm01/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and H(z.read(f'm01/exchange/image-{i}.png'))==req['image_sha256']==resp['image_sha256'];assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed' and raw['call_id'] not in ids;ids.add(raw['call_id']);session=session or raw['thread_id'];assert raw['thread_id']==session;calls.append(raw['usage'])
 print(json.dumps({'status':'audited','outcome':'SAFE_YIELD','reobservations':len(recorded),'capture_span_seconds':(captures[-1]-captures[0])/1e9,'fresh_actions':0,'saved_values':[],'final_neutral':True,'usage':{k:sum(x[k] for x in calls) for k in ['input_tokens','cached_input_tokens','output_tokens']}},indent=2))
