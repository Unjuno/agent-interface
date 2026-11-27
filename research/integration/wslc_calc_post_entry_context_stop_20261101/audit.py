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

p=Path(__file__).with_name('public.zip');H=lambda b:hashlib.sha256(b).hexdigest();assert H(p.read_bytes())=='4fc3df1343e39b423001983098b5a42ddfd4db0505d7064f332731a03ea77d6d'
with ZipFile(p) as z:
 m=read(z,'manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 c=read(z,'k01/conditions.json');assert c['allocation']=='k01' and c['route']=='compiled' and c['calls_max']==2
 for n,h in c['candidate'].items():assert H(z.read('candidate/'+n))==h
 assert H(z.read('candidate/launcher.py'))==c['launcher_sha256'] and H(z.read('source-hashes.json'))==c['source_manifest_sha256']
 v=read(z,'verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 launch=read(z,'k01/launcher-result.json');assert launch['container_exit']==launch['host_exit']==0 and not launch['live_handle_unresolved']
 result=read(z,'k01/output/result.json');r=result['method']['method_receipt'];assert r['outcome']=='SAFE_YIELD' and r['reason']=='effect_unavailable' and r['completed_transitions']==1 and len(r['transitions'])==1 and r['transitions'][0]['action']=='enter' and r['transitions'][0]['release_verified'] and r['pending_effect']['action']=='enter' and r['pending_effect']['effect_ref']==r['transitions'][0]['effect_ref']
 assert r['observations'][-1]['predicates']['context_ok'] is False and r['observations'][-1]['predicates']['cells_filled']=='unknown'
 names=z.namelist();executions=[n for n in names if n.startswith('k01/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1
 programs=[read(z,n) for n in names if n.startswith('k01/output/owner/') and '/program-' in n and n.endswith('.json')];assert len(programs)==2 and sum(any(op.get('op')=='text' for op in program['ops']) for program in programs)==1 and not any(op.get('op')=='key_chord' and op.get('keys')==['CTRL','s'] for program in programs for op in program['ops'])
 ex=read(z,executions[0]);assert ex['request']['action']=='enter' and ex['action_id']==r['transitions'][0]['action_id'] and ex['result']['status']=='completed' and release(ex['result'])
 injection=read(z,'k01/output/post-entry-invalidation.json');assert len(injection['injected'])==1 and injection['injected'][0]['alias']=='entry' and injection['injected'][0]['status']=='completed' and injection['injected'][0]['release']==ex['result']['execution']['releases'] and injection['cell_cue']=='filled' and injection['context_changed'] is True
 native=injection['post_observation'];artifact=native['native']['artifact'];payload=z.read('k01/output/'+artifact['path'].removeprefix('/out/'));assert H(payload)==artifact['sha256'];screen=Image.open(BytesIO(payload)).convert('RGB');reference=Image.open(BytesIO(z.read('candidate/reference.png'))).convert('RGB');initial=Image.open(BytesIO(z.read('k01/exchange/image-1.png'))).convert('RGB')
 assert all(screen.crop(box).tobytes()==reference.crop(box).tobytes() for box in [(100,145,123,157),(100,162,123,174)]) and screen.crop((350,20,370,35)).tobytes()!=initial.crop((350,20,370,35)).tobytes()
 assert z.read('k01/output/saved.fods')==z.read('candidate/blank.fods') and vals(z.read('k01/output/saved.fods'))==[] and result['saved_score']['populated']==[]
 assert result['close']['status']=='closed' and result['close']['release']['verified'] and not result['close']['release']['keys_down'] and not result['close']['release']['buttons_down'] and not result['keys_down'] and not result['buttons']
 calls=[];session=None;ids=set()
 for i in (1,2):
  req=read(z,f'k01/exchange/request-{i}.json');resp=read(z,f'k01/exchange/response-{i}.json');raw=read(z,f'k01/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and H(z.read(f'k01/exchange/image-{i}.png'))==req['image_sha256']==resp['image_sha256'];assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed' and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['call_id'] not in ids;ids.add(raw['call_id']);session=session or raw['thread_id'];assert raw['thread_id']==session;calls.append(raw['usage'])
 assert len([n for n in names if n.startswith('k01/exchange/response-') and n.endswith('.json')])==2
 print(json.dumps({'status':'audited','outcome':r['outcome'],'pending_effect':r['pending_effect']['action'],'completed_entries':1,'in_memory_pixel_cue':'filled','saved_values':[],'neutral':True,'usage':{k:sum(x[k] for x in calls) for k in ['input_tokens','cached_input_tokens','output_tokens']}},indent=2))
