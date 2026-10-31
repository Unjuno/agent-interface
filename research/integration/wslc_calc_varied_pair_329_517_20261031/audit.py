"""Audit passive Calc reference and two independent saved-file outcomes."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,xml.etree.ElementTree as ET
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
def values(blob):
 sheets=ET.fromstring(blob).findall('.//'+T+'table');assert len(sheets)==1
 sheet=sheets[0];rows=sheet.findall(T+'table-row');assert len(rows)==len(sheet.findall('.//'+T+'table-row'))
 found=[];row_index=0
 for row in rows:
  repeat=int(row.get(T+'number-rows-repeated','1'));assert repeat>0;col=0
  for cell in row:
   if cell.tag not in (T+'table-cell',T+'covered-table-cell'):continue
   count=int(cell.get(T+'number-columns-repeated','1'));assert count>0
   kind=cell.get(O+'value-type');value=cell.get(O+'value');formula=cell.get(T+'formula');text=''.join(cell.itertext()).strip()
   if kind is not None or value is not None or formula is not None or text:
    assert repeat==1 and count==1;found.append((row_index,col,kind,value,text,formula))
   col+=count
  row_index+=repeat
 return found
expected=[(0,0,'float','329','329',None),(1,0,'float','517','517',None)]
def release(row):
 a=row['execution']['releases'];return bool(a) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in a)
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='99ff8ee1e8940e3c88142c54638dbf94334dea132390bbc88d91fa2dd4f5a134'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not any(v['input_mismatches'].values()) and v['list_exit']==0 and not v['present']
 c=j('d01/conditions.json');r=j('d01/out/result.json');l=j('d01/out/launcher.json')
 assert c['allocation']=='d01' and hashlib.sha256(z.read('d01/blank.fods')).hexdigest()==c['fixture_sha256'] and values(z.read('d01/blank.fods'))==expected
 assert hashlib.sha256(z.read('d01/runner.py')).hexdigest()==c['runner_sha256'] and l['exit_code']==0 and not l['timeout']
 assert r['status']=='observed' and r['input_dispatched'] is False and not r['keys_down'] and r['buttons']==0
 artifact=r['observation']['native']['artifact'];reference=z.read('d01/'+artifact['path'].lstrip('/'));assert hashlib.sha256(reference).hexdigest()==artifact['sha256'] and len(reference)==artifact['bytes']
 sessions=set();all_ids=set();base_hashes=None;results=[]
 for tag,route,count in [('d02','fresh',2),('d03','compiled',1)]:
  c=j(f'{tag}/conditions.json');run=j(f'{tag}/launcher-result.json');r=j(f'{tag}/output/result.json')
  assert c['allocation']==tag and c['route']==route and c['fixture']==['329','517'] and c['order']==['d02:fresh','d03:compiled']
  assert run['container_exit']==run['host_exit']==0 and run['timeout'] is False
  for n,h in c['input_sha256'].items():assert hashlib.sha256(z.read(f'{tag}/{n}')).hexdigest()==h,n
  if base_hashes is None:base_hashes=c['input_sha256']
  else:assert base_hashes==c['input_sha256']
  assert z.read(f'{tag}/reference.png')==reference
  assert r['route']==route and r['saved_score']['pass_effect'] and values(z.read(f'{tag}/output/saved.fods'))==expected
  assert not r['keys_down'] and r['buttons']==0 and r['close']['status']=='closed' and r['close']['release_attempted'] and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  assert r['task_start_ns']<r['method_start_ns']<r['method_end_ns']<r['task_end_ns']
  click=j(f'{tag}/output/click-result.json');assert click['status']=='completed' and release(click)
  usage=[];session=None
  for i in range(1,count+1):
   req=j(f'{tag}/exchange/request-{i}.json');resp=j(f'{tag}/exchange/response-{i}.json');raw=j(f'{tag}/model-call-{i}/result.json')
   assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and hashlib.sha256(z.read(f'{tag}/exchange/image-{i}.png')).hexdigest()==req['image_sha256']==resp['image_sha256']
   assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed' and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low'
   assert raw['call_id'] not in all_ids;all_ids.add(raw['call_id']);usage.append(raw['usage'])
   if session is None:session=raw['thread_id']
   else:assert session==raw['thread_id']
   assert resp.get('close_returned',False)==(i==count) and 0<=raw['usage']['cached_input_tokens']<=raw['usage']['input_tokens']
  assert session not in sessions;sessions.add(session)
  if route=='compiled':
   rec=r['method']['method_receipt'];assert rec['outcome']=='TASK_SUCCEEDED' and len(rec['transitions'])==2 and all(x['release_verified'] for x in rec['transitions'])
   assert j(f'{tag}/output/method/saved-effect.json')['verdict']['status']=='succeeded'
  else:
   assert r['method']['status']=='completed';guard=j(f'{tag}/output/fresh-semantic-guard.json');assert guard['events'][0]['event']=='armed' and guard['cue']['cue']=='filled'
   for n in ('fresh-entry.json','fresh-save.json'):
    item=j(f'{tag}/output/{n}');assert item['status']=='completed' and release(item)
  results.append({'allocation':tag,'route':route,'task_seconds':(r['task_end_ns']-r['task_start_ns'])/1e9,'input_tokens':sum(u['input_tokens'] for u in usage),'cached_input_subset':sum(u['cached_input_tokens'] for u in usage),'output_tokens':sum(u['output_tokens'] for u in usage),'model_calls':count})
 print(json.dumps({'status':'audited','reference':'passive prepopulated fixture','results':results},indent=2))
