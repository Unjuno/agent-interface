"""Audit two one-shot Calc cue reconciliation controls and saved effects."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
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
def releases(row):
 a=row['execution']['releases'];return bool(a) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in a)
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='fe38fdc05bcf378be6c3de635580b8a59d3a7ea3267858583091beeca955b8ef'
prior=p.parent.parent/'wslc_calc_varied_pair_329_517_20261031'/'public.zip';assert hashlib.sha256(prior.read_bytes()).hexdigest()=='99ff8ee1e8940e3c88142c54638dbf94334dea132390bbc88d91fa2dd4f5a134'
negative=p.parent.parent/'wslc_calc_stale_reference_20261031'/'public.zip';assert hashlib.sha256(negative.read_bytes()).hexdigest()=='76f38518540286f9b72d976069ecfd45e8d5334dbe7fa493eeec21a3e31ef439'
with ZipFile(p) as z,ZipFile(prior) as old,ZipFile(negative) as stale:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not any(v['input_mismatches'].values()) and v['list_exit']==0 and not v['present']
 c0=j('d05/conditions.json');c1=j('d06/conditions.json');a=c0['input_sha256'];b=c1['input_sha256'];assert set(a)==set(b) and [n for n in a if a[n]!=b[n]]==['recovery-reference.png']
 assert z.read('d05/reference.png')==z.read('d06/reference.png')==stale.read('reference.png')==z.read('d05/recovery-reference.png')
 assert z.read('d06/recovery-reference.png')==old.read('d03/reference.png')
 img_a=Image.open(BytesIO(z.read('d05/recovery-reference.png'))).convert('RGB');img_b=Image.open(BytesIO(z.read('d06/recovery-reference.png'))).convert('RGB')
 for box in ((100,145,123,157),(100,162,123,174)):assert img_a.crop(box).tobytes()!=img_b.crop(box).tobytes()
 summaries=[];ids=set()
 for tag,mode,expected_cue in [('d05','reject_stale','unknown'),('d06','verified_save','filled')]:
  c=j(f'{tag}/conditions.json');l=j(f'{tag}/launcher-result.json');r=j(f'{tag}/output/result.json');q=j(f'{tag}/output/recovery.json');method=r['method'];rec=method['method_receipt']
  assert c['allocation']==tag and c['mode']==mode and c['order']==['d05:reject_stale','d06:verified_save']
  for n,h in c['input_sha256'].items():assert hashlib.sha256(z.read(f'{tag}/{n}')).hexdigest()==h,n
  assert l['container_exit']==l['host_exit']==0 and l['timeout'] is False
  assert rec['outcome']=='SAFE_YIELD' and rec['reason']=='effect_unavailable' and rec['pending_effect']['action']=='enter' and [x['action'] for x in rec['transitions']]==['enter'] and rec['transitions'][0]['release_verified']
  assert method['task_success'] is None and method['replay_allowed'] is False and r['recovery']==q and q['original_replay_allowed'] is False and q['entry_replayed'] is False and q['max_attempts']==1
  assert q['cue']==expected_cue and q['new_observation_sequence']>rec['observations'][-1]['sequence']
  artifact=q['observation']['native']['artifact'];image=z.read(f"{tag}/output/"+artifact['path'].removeprefix('/out/'));assert len(image)==artifact['bytes'] and hashlib.sha256(image).hexdigest()==artifact['sha256']
  observed=Image.open(BytesIO(image)).convert('RGB');reviewed=Image.open(BytesIO(z.read(f'{tag}/recovery-reference.png'))).convert('RGB')
  matches=all(observed.crop(box).tobytes()==reviewed.crop(box).tobytes() for box in ((100,145,123,157),(100,162,123,174)))
  assert matches==(expected_cue=='filled')
  executions=[n for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1
  e=j(executions[0]);assert e['request']['action']=='enter' and e['result']['status']=='completed' and releases(e['result'])
  click=j(f'{tag}/output/click-result.json');assert click['status']=='completed' and releases(click)
  mints=[n for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('/mint-recovery_save.json')]
  if mode=='reject_stale':
   assert q['save_attempted'] is False and q['save_completed'] is False and not mints and f'{tag}/output/recovery-save.json' not in z.namelist()
   assert z.read(f'{tag}/output/saved.fods')==z.read(f'{tag}/blank.fods') and r['saved_score']['pass_effect'] is False
  else:
   assert q['save_attempted'] is True and q['save_completed'] is True and len(mints)==1
   save=j(f'{tag}/output/recovery-save.json');guard=j(f'{tag}/output/recovery-guard.json')
   assert save['status']=='completed' and releases(save) and save['guard_checks'] and all(x['status']=='VALID' and x['eligible'] for x in save['guard_checks'])
   assert guard['events'][0]['event']=='armed' and guard['cue']['cue']=='filled' and guard['cue']['sequence']==q['new_observation_sequence']
   assert r['saved_score']['pass_effect'] and values(z.read(f'{tag}/output/saved.fods'))==expected
  assert not r['keys_down'] and r['buttons']==0 and r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  req=j(f'{tag}/exchange/request-1.json');resp=j(f'{tag}/exchange/response-1.json');raw=j(f'{tag}/model-call-1/result.json')
  assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and resp['close_returned'] and hashlib.sha256(z.read(f'{tag}/exchange/image-1.png')).hexdigest()==req['image_sha256']==resp['image_sha256']
  assert raw['call_id']==resp['call_id'] and raw['call_id'] not in ids and raw['usage']==resp['usage'] and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['turn_status']=='completed';ids.add(raw['call_id'])
  assert f'{tag}/exchange/request-2.json' not in z.namelist();u=raw['usage'];assert 0<=u['cached_input_tokens']<=u['input_tokens']
  summaries.append({'allocation':tag,'mode':mode,'original':'SAFE_YIELD','fresh_cue':q['cue'],'new_save':q['save_completed'],'input_tokens':u['input_tokens'],'cached_input_subset':u['cached_input_tokens'],'output_tokens':u['output_tokens']})
 print(json.dumps({'status':'audited','results':summaries},indent=2))
