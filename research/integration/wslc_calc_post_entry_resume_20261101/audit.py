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

p=Path(__file__).with_name('public.zip');H=lambda b:hashlib.sha256(b).hexdigest();assert H(p.read_bytes())=='bee00aa3b2257cf7bdffb6f70c60eb8df2fc9d256f4d0d1ce3deeee53dc00576'
with ZipFile(p) as z:
 m=read(z,'manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 v=read(z,'verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 rows=[];sessions=set()
 def image(tag,native):
  a=native['native']['artifact'];blob=z.read(tag+'/output/'+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'];return Image.open(BytesIO(blob)).convert('RGB')
 for tag in ['l01','l02']:
  c=read(z,tag+'/conditions.json');assert c['allocation']==tag and c['route']=='compiled' and c['calls_max']==2
  for n,h in c['candidate'].items():assert H(z.read(tag+'/candidate/'+n))==h
  assert H(z.read(tag+'/candidate/launcher.py'))==c['launcher_sha256'] and H(z.read('source-hashes.json'))==c['source_manifest_sha256']
  launch=read(z,tag+'/launcher-result.json');assert launch['host_exit']==0 and not launch['live_handle_unresolved'] and launch['container_exit']==(1 if tag=='l01' else 0)
  original=read(z,tag+'/output/method/result.json')['method_receipt'];assert original['outcome']=='SAFE_YIELD' and original['reason']=='effect_unavailable' and original['completed_transitions']==1 and len(original['transitions'])==1 and original['transitions'][0]['action']=='enter' and original['transitions'][0]['release_verified'] and original['pending_effect']['effect_ref']==original['transitions'][0]['effect_ref']
  executions=[n for n in z.namelist() if n.startswith(tag+'/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1
  action=read(z,executions[0]);assert action['request']['action']=='enter' and action['result']['status']=='completed' and release(action['result']) and action['action_id']==original['transitions'][0]['action_id']
  post=read(z,tag+'/output/post-entry-invalidation.json');assert len(post['injected'])==1 and post['cell_cue']=='filled' and post['context_changed'] and post['injected'][0]['release']==action['result']['execution']['releases']
  screen=image(tag,post['post_observation']);reference=Image.open(BytesIO(z.read(tag+'/candidate/reference.png'))).convert('RGB');first=Image.open(BytesIO(z.read(tag+'/exchange/image-1.png'))).convert('RGB');boxes=[(100,145,123,157),(100,162,123,174)];context=(350,20,370,35);assert all(screen.crop(b).tobytes()==reference.crop(b).tobytes() for b in boxes) and screen.crop(context).tobytes()!=first.crop(context).tobytes()
  obs=[n for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and n.endswith('/observation-1.json')];assert len(obs)==1;fresh=read(z,obs[0]);fresh_image=image(tag,fresh);assert all(fresh_image.crop(b).tobytes()==reference.crop(b).tobytes() for b in boxes)
  calls=[];session=None;ids=set()
  for i in (1,2):
   req=read(z,f'{tag}/exchange/request-{i}.json');resp=read(z,f'{tag}/exchange/response-{i}.json');raw=read(z,f'{tag}/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and H(z.read(f'{tag}/exchange/image-{i}.png'))==req['image_sha256']==resp['image_sha256'];assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed' and raw['call_id'] not in ids and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low';ids.add(raw['call_id']);session=session or raw['thread_id'];assert raw['thread_id']==session;calls.append(raw['usage'])
  assert session not in sessions;sessions.add(session)
  if tag=='l01':
   assert fresh_image.crop(context).tobytes()!=first.crop(context).tobytes();assert 'fresh recovered state unavailable' in z.read(tag+'/container.stderr').decode();assert not any(n.startswith(tag+'/output/recovery-owner/') and ('/mint-' in n or '/program-' in n) for n in z.namelist());neutral=read(z,tag+'/output/final-neutral.json');assert neutral['close']['status']=='closed' and not neutral['keys_down'] and not neutral['buttons'];assert tag+'/output/recovery-save.json' not in z.namelist();effect='not recorded'
  else:
   result=read(z,tag+'/output/result.json');rec=read(z,tag+'/output/recovery.json');assert rec['entry_replayed'] is False and rec['save_effect']=='unverified' and rec['prior_close']['session_id']!=rec['fresh_session_id'] and rec['fresh_session_id']==result['close']['session_id'] and rec['prior_close']['release']['verified'] and not rec['prior_close']['release']['keys_down'] and not rec['prior_close']['release']['buttons_down'];assert fresh['native']['artifact']['sha256']==rec['fresh_observation']['native']['artifact']['sha256'] and fresh_image.crop(context).tobytes()==first.crop(context).tobytes()
   observations=read(z,tag+'/output/reobservations.json');assert len(observations)==1 and observations[0]=={'sequence':1,'filled':True,'context_ok':True}
   save=read(z,tag+'/output/recovery-save.json');assert save['status']=='completed' and save['recovery_required'] is False and release(save) and all(x['eligible'] for x in save['additional_input_checks']);guard=read(z,tag+'/output/recovery-guard.json');assert guard['cue']['sequence']==fresh['sequence'] and guard['cue']['artifact_sha256']==fresh['native']['artifact']['sha256'] and guard['events'][0]['event']=='armed'
   programs=[read(z,n) for n in z.namelist() if n.startswith(tag+'/output/recovery-owner/') and '/program-' in n and n.endswith('.json')];assert len(programs)==1 and sum(op.get('op')=='key_chord' and op.get('keys')==['CTRL','s'] for op in programs[0]['ops'])==1 and not any(op.get('op')=='text' for op in programs[0]['ops'])
   assert vals(z.read(tag+'/output/saved.fods'))==[(0,0,'float','731','731',None),(1,0,'float','864','864',None)] and result['saved_score']['pass_effect'] and result['close']['release']['verified'] and not result['close']['release']['keys_down'] and not result['close']['release']['buttons_down'] and not result['keys_down'] and not result['buttons'];effect='exact 731/864'
  rows.append({'allocation':tag,'original':'SAFE_YIELD','recovery_save':tag=='l02','saved_effect':effect,'final_x_neutral':True,'usage':{k:sum(x[k] for x in calls) for k in ['input_tokens','cached_input_tokens','output_tokens']}})
 print(json.dumps({'status':'audited','results':rows},indent=2))
