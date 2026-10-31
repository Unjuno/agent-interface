"""Audit Calc late-clear, adversarial deadline race and fix; no -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json,xml.etree.ElementTree as ET
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}';O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
def vals(blob):
 sheets=ET.fromstring(blob).findall('.//'+T+'table');assert len(sheets)==1
 sheet=sheets[0];rows=sheet.findall(T+'table-row');assert len(rows)==len(sheet.findall('.//'+T+'table-row'));populated=[];ri=0
 for row in rows:
  repeat=int(row.get(T+'number-rows-repeated','1'));assert repeat>0;col=0
  for cell in row:
   if cell.tag not in (T+'table-cell',T+'covered-table-cell'):continue
   count=int(cell.get(T+'number-columns-repeated','1'));assert count>0;kind=cell.get(O+'value-type');value=cell.get(O+'value');formula=cell.get(T+'formula');text=''.join(cell.itertext()).strip()
   if kind is not None or value is not None or formula is not None or text:assert repeat==1 and count==1;populated.append((ri,col,kind,value,text,formula))
   col+=count
  ri+=repeat
 return populated
def release(row):
 xs=row['execution']['releases'];return bool(xs) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in xs)
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='113676b31244af6ae7364114ffd1499723c8799eae26867d65286cce88fa8930'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['source_files_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 old=z.read('race/candidate/runner.py').decode().replace('\r\n','\n');fixed=z.read('fixed/candidate/runner.py').decode().replace('\r\n','\n')
 before="   if filled and context_ok:break\n   if time.monotonic()>=until:raise RuntimeError('fresh recovered state unavailable after bounded reobservation')"
 after="   if time.monotonic_ns()>=until_ns:raise RuntimeError('fresh recovered state unavailable after bounded reobservation')\n   if filled and context_ok:break"
 assert old.count(before)==1 and old.replace(before,after)==fixed
 sessions=set()
 for tag,arm,expected_exit in [('late','eg01',1),('race','eh01',0),('fixed','ei01',1)]:
  c=j(tag+'/conditions.json');assert c['allocation']==arm and c['route']=='compiled' and H(z.read('source-hashes.json'))==c['source_manifest_sha256'] and H(z.read(tag+'/candidate/launcher.py'))==c['launcher_sha256']
  for n,h in c['candidate'].items():assert H(z.read(tag+'/candidate/'+n))==h,n
  launch=j(tag+'/launcher-result.json');assert launch['container_exit']==expected_exit and launch['host_exit']==0 and not launch['live_handle_unresolved']
  calls=[];ids=set();session=None
  for i in (1,2):
   req=j(f'{tag}/exchange/request-{i}.json');resp=j(f'{tag}/exchange/response-{i}.json');raw=j(f'{tag}/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and H(z.read(f'{tag}/exchange/image-{i}.png'))==req['image_sha256']==resp['image_sha256'] and raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed' and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['call_id'] not in ids;ids.add(raw['call_id']);session=session or raw['thread_id'];assert raw['thread_id']==session;calls.append(raw['usage'])
  assert session not in sessions;sessions.add(session)
  receipt=j(tag+'/output/method/result.json')['method_receipt'];assert receipt['outcome']=='SAFE_YIELD' and receipt['reason']=='effect_unavailable' and receipt['completed_transitions']==1 and len(receipt['transitions'])==1 and receipt['transitions'][0]['action']=='enter' and receipt['transitions'][0]['release_verified'];executions=[n for n in z.namelist() if n.startswith(tag+'/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1;entry=j(executions[0]);assert entry['request']['action']=='enter' and entry['result']['status']=='completed' and release(entry['result']) and entry['action_id']==receipt['transitions'][0]['action_id'];prior=j(tag+'/output/prior-close.json');assert prior['status']=='closed' and prior['release']['verified'] and not prior['release']['keys_down'] and not prior['release']['buttons_down']
  reference=Image.open(BytesIO(z.read(tag+'/candidate/reference.png'))).convert('RGB');original=Image.open(BytesIO(z.read(tag+'/exchange/image-1.png'))).convert('RGB');boxes=[(100,145,123,157),(100,162,123,174)];context=(350,20,370,35);observations=j(tag+'/output/reobservations.json')
  for row in observations:
   names=[n for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and n.endswith(f"/observation-{row['sequence']}.json")];assert len(names)==1;obs=j(names[0]);a=obs['native']['artifact'];blob=z.read(tag+'/output/'+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'];image=Image.open(BytesIO(blob)).convert('RGB');filled=all(image.crop(b).tobytes()==reference.crop(b).tobytes() for b in boxes);context_ok=image.crop(context).tobytes()==original.crop(context).tobytes();assert row['filled']==filled and row['context_ok']==context_ok
  if tag=='late':
   e=j(tag+'/output/late-clear.json');assert e['deadline_ns']<=e['expired_ns']<=e['cleared_ns']<e['end_ns'] and e['end_ns']-e['cleared_ns']>=500_000_000 and all(not row['filled'] for row in observations) and len(e['observations'])>=2
   for row in e['observations']:
    names=[n for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and n.endswith(f"/observation-{row['sequence']}.json")];assert len(names)==1;obs=j(names[0]);a=obs['native']['artifact'];blob=z.read(tag+'/output/'+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'];image=Image.open(BytesIO(blob)).convert('RGB');assert row['filled'] and row['context_ok'] and obs['capture_ns']>e['cleared_ns'] and all(image.crop(b).tobytes()==reference.crop(b).tobytes() for b in boxes) and image.crop(context).tobytes()==original.crop(context).tobytes()
  else:
   e=j(tag+'/output/race-event.json');last=observations[-1];assert len(observations)==e['observations_before']+1 and all(not x['filled'] for x in observations[:-1]) and last['filled'] and last['context_ok'] and e['clear_ns']>=e['deadline_ns']+50_000_000
   names=[n for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and n.endswith(f"/observation-{last['sequence']}.json")];assert len(names)==1;lastobs=j(names[0]);assert lastobs['capture_ns']>e['clear_ns']
  fresh_mints=[n for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and '/mint-' in n];programs=[n for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and '/program-' in n and n.endswith('.json')]
  if tag=='race':
   result=j(tag+'/output/result.json');save=j(tag+'/output/recovery-save.json');assert len(fresh_mints)==len(programs)==1 and save['status']=='completed' and release(save) and save['execution']['started_ns']>e['deadline_ns'];assert [x['stage'] for x in save['additional_input_checks']]==['before_admission','before_focus','before_key_press:CTRL','before_key_press:s'] and all(x['eligible'] for x in save['additional_input_checks']);ops=j(programs[0])['ops'];assert sum(op.get('op')=='key_chord' and op.get('keys')==['CTRL','s'] for op in ops)==1 and not any(op.get('op')=='text' for op in ops);assert vals(z.read(tag+'/output/saved.fods'))==[(0,0,'float','731','731',None),(1,0,'float','864','864',None)] and result['close']['release']['verified'] and not result['keys_down'] and not result['buttons'];outcome='late Save dispatched';delay=(save['execution']['started_ns']-e['deadline_ns'])/1e6
  else:
   assert not fresh_mints and not programs and tag+'/output/recovery-save.json' not in z.namelist();neutral=j(tag+'/output/final-neutral.json');assert neutral['close']['status']=='closed' and neutral['close']['session_id']!=prior['session_id'] and not neutral['keys_down'] and not neutral['buttons'];blob=z.read(tag+'/output/finally-saved.fods');assert blob==z.read(tag+'/candidate/blank.fods') and vals(blob)==[];outcome='no recovery input';delay=None
  print(json.dumps({'allocation':arm,'outcome':outcome,'observations':len(observations),'late_save_after_deadline_ms':delay,'final_neutral':True,'input_tokens':sum(x['input_tokens'] for x in calls),'output_tokens':sum(x['output_tokens'] for x in calls)}))
