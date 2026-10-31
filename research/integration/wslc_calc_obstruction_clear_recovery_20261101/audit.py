"""Audit bounded Calc obstruction clear and guarded Save; no -O."""
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
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='f7a3a61864e3e13cc54be7764b1a873fe56ea5f20ab9bb16481a04a0c82f1c38'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 c=j('ef01/conditions.json');v=j('verification.json');assert c['allocation']=='ef01' and c['route']=='compiled' and H(z.read('source-hashes.json'))==c['source_manifest_sha256'] and v['source_files_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty'];assert H(z.read('candidate/launcher.py'))==c['launcher_sha256']
 for n,h in c['candidate'].items():assert H(z.read('candidate/'+n))==h,n
 launch=j('ef01/launcher-result.json');assert launch['container_exit']==launch['host_exit']==0 and not launch['live_handle_unresolved']
 calls=[];ids=set();session=None
 for i in (1,2):
  req=j(f'ef01/exchange/request-{i}.json');resp=j(f'ef01/exchange/response-{i}.json');raw=j(f'ef01/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and H(z.read(f'ef01/exchange/image-{i}.png'))==req['image_sha256']==resp['image_sha256'] and raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed' and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['call_id'] not in ids;ids.add(raw['call_id']);session=session or raw['thread_id'];assert raw['thread_id']==session;calls.append(raw['usage'])
 r=j('ef01/output/result.json');receipt=j('ef01/output/method/result.json')['method_receipt'];assert receipt['outcome']=='SAFE_YIELD' and receipt['reason']=='effect_unavailable' and receipt['completed_transitions']==1 and len(receipt['transitions'])==1 and receipt['transitions'][0]['action']=='enter' and receipt['transitions'][0]['release_verified'] and receipt['pending_effect']['effect_ref']==receipt['transitions'][0]['effect_ref']
 executions=[n for n in z.namelist() if n.startswith('ef01/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1;entry=j(executions[0]);assert entry['request']['action']=='enter' and entry['result']['status']=='completed' and release(entry['result']) and entry['action_id']==receipt['transitions'][0]['action_id']
 post=j('ef01/output/post-entry-invalidation.json');assert len(post['injected'])==1 and post['cell_cue']=='filled' and post['context_changed'] and post['injected'][0]['release']==entry['result']['execution']['releases']
 prior=j('ef01/output/prior-close.json');rec=j('ef01/output/recovery.json');assert prior==rec['prior_close'] and prior['status']=='closed' and prior['release']['verified'] and not prior['release']['keys_down'] and not prior['release']['buttons_down'] and rec['fresh_session_id']!=prior['session_id'] and rec['entry_replayed'] is False and rec['save_effect']=='unverified'
 reference=Image.open(BytesIO(z.read('candidate/reference.png'))).convert('RGB');original=Image.open(BytesIO(z.read('ef01/exchange/image-1.png'))).convert('RGB');boxes=[(100,145,123,157),(100,162,123,174)];context=(350,20,370,35);events=j('ef01/output/obstruction-events.json');observations=j('ef01/output/reobservations.json');assert events['cleared_ns']-events['mapped_ns']>=650_000_000 and events['failed_observations_before_clear']>=2 and len(observations)==events['failed_observations_before_clear']+1
 for index,row in enumerate(observations):
  names=[n for n in z.namelist() if n.startswith('ef01/output/recovery-owner/') and n.endswith(f"/observation-{row['sequence']}.json")];assert len(names)==1;obs=j(names[0]);a=obs['native']['artifact'];blob=z.read('ef01/output/'+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'];image=Image.open(BytesIO(blob)).convert('RGB');filled=all(image.crop(b).tobytes()==reference.crop(b).tobytes() for b in boxes);context_ok=image.crop(context).tobytes()==original.crop(context).tobytes();assert row['filled']==filled and row['context_ok']==context_ok
  if index<len(observations)-1:assert not filled and events['mapped_ns']<=obs['capture_ns']<events['cleared_ns']
  else:assert filled and context_ok and obs['capture_ns']>events['cleared_ns'] and a['sha256']==rec['fresh_observation']['native']['artifact']['sha256']
 save=j('ef01/output/recovery-save.json');assert save['status']=='completed' and save['recovery_required'] is False and release(save) and [x['stage'] for x in save['additional_input_checks']]==['before_admission','before_focus','before_key_press:CTRL','before_key_press:s'] and all(x['eligible'] for x in save['additional_input_checks']);guard=j('ef01/output/recovery-guard.json');assert guard['cue']['sequence']==rec['fresh_observation']['sequence'] and guard['cue']['artifact_sha256']==rec['fresh_observation']['native']['artifact']['sha256'] and guard['events'][0]['event']=='armed'
 programs=[j(n) for n in z.namelist() if n.startswith('ef01/output/recovery-owner/') and '/program-' in n and n.endswith('.json')];assert len(programs)==1 and sum(op.get('op')=='key_chord' and op.get('keys')==['CTRL','s'] for op in programs[0]['ops'])==1 and not any(op.get('op')=='text' for op in programs[0]['ops']);assert save['execution']['started_ns']>events['cleared_ns']
 assert vals(z.read('ef01/output/saved.fods'))==[(0,0,'float','731','731',None),(1,0,'float','864','864',None)] and r['saved_score']['pass_effect'] and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down'] and not r['buttons']
 print(json.dumps({'status':'audited','blocked_ms':(events['cleared_ns']-events['mapped_ns'])/1e6,'failed_observations':events['failed_observations_before_clear'],'fresh_capture_after_clear_ms':(rec['fresh_observation']['capture_ns']-events['cleared_ns'])/1e6,'entry_executions':len(executions),'recovery_programs':len(programs),'saved':'731/864','final_neutral':True,'usage':{k:sum(x[k] for x in calls) for k in ('input_tokens','cached_input_tokens','output_tokens')}},indent=2))
