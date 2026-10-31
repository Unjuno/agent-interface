"""Audit a real direct-child timeout and live, bounded Calc OCR recovery."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO,StringIO
from PIL import Image,ImageOps
import csv,hashlib,json,math,re,xml.etree.ElementTree as ET
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}';O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
def values(blob):
 sheets=ET.fromstring(blob).findall('.//'+T+'table');assert len(sheets)==1
 sheet=sheets[0];rows=sheet.findall(T+'table-row');assert len(rows)==len(sheet.findall('.//'+T+'table-row'));found=[];ri=0
 for row in rows:
  repeat=int(row.get(T+'number-rows-repeated','1'));assert repeat>0;col=0
  for cell in row:
   if cell.tag not in (T+'table-cell',T+'covered-table-cell'):continue
   count=int(cell.get(T+'number-columns-repeated','1'));assert count>0
   kind=cell.get(O+'value-type');value=cell.get(O+'value');formula=cell.get(T+'formula');text=''.join(cell.itertext()).strip()
   if kind is not None or value is not None or formula is not None or text:
    assert repeat==1 and count==1;found.append((ri,col,kind,value,text,formula))
   col+=count
  ri+=repeat
 return found
expected=[(0,0,'float','329','329',None),(1,0,'float','517','517',None)]
def release(row):
 a=row['execution']['releases'];return bool(a) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in a)
def read_word(blob):
 reader=csv.DictReader(StringIO(blob.decode()),delimiter='\t');assert {'level','conf','text'}.issubset(reader.fieldnames or []);words=[]
 for row in reader:
  text=(row.get('text') or '').strip()
  if not text:continue
  try:confidence=float(row['conf'])
  except (ValueError,KeyError):return None
  if row.get('level')!='5' or not math.isfinite(confidence) or not 90<=confidence<=100 or not re.fullmatch('[0-9]+',text):return None
  words.append(text)
 return words[0] if len(words)==1 else None
def cue(a,b):
 x,y=read_word(a),read_word(b)
 return 'unknown' if x is None or y is None else ('filled' if (x,y)==('329','517') else 'wrong')
def crop_png(image,box):
 crop=image.crop(box);crop.putdata([(255,255,255) if b>r+30 and b>g+20 else (r,g,b) for r,g,b in crop.getdata()]);crop=crop.convert('L').resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS);crop=ImageOps.expand(crop,border=16,fill=255);buf=BytesIO();crop.save(buf,format='PNG');return buf.getvalue()
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='8d39036d6d086c4e587a55a0347f137f7abba4b95727ee48e7ca442d5b4c8126'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not any(v['input_mismatches'].values()) and v['list_exit']==0 and not v['present']
 src=j('source-hashes.json');pre=j('source-precheck.json');assert len(src)==pre['files']==2092 and not pre['other_mismatches'] and pre['main_commit']=='9ad6c0099c44f6be901e7310866b8ea4b70a46a7' and pre['source_manifest_sha256']==hashlib.sha256(z.read('source-hashes.json')).hexdigest()
 c0=j('e08/conditions.json');c1=j('e09/conditions.json');assert c0['input_sha256']==c1['input_sha256'] and 'recovery-reference.png' not in c0['input_sha256']
 results=[];ids=set();command=['tesseract','stdin','stdout','--psm','7','-c','tessedit_char_whitelist=0123456789','tsv']
 for tag,mode,expected_cue in [('e08','slow_child','unknown'),('e09','clear','filled')]:
  c=j(f'{tag}/conditions.json');l=j(f'{tag}/launcher-result.json');r=j(f'{tag}/output/result.json');q=j(f'{tag}/output/recovery.json');method=r['method'];rec=method['method_receipt'];ocr=j(f'{tag}/output/recovery-ocr/001.json');attempts=j(f'{tag}/output/ocr-attempts.json')
  assert c['allocation']==tag and c['mode']==mode and c['order']==['e08:slow_child','e09:clear'] and c['source_manifest_sha256']==pre['source_manifest_sha256']
  for n,h in c['input_sha256'].items():assert hashlib.sha256(z.read(f'{tag}/{n}')).hexdigest()==h,n
  assert hashlib.sha256(z.read(f'{tag}/study/ocr_attempt_recorder_v1.py')).hexdigest()=='396e32e427236c3f2fa93a3409ab8f79ba531b064ae7efc90094ff55c060e09f'
  assert l['container_exit']==l['host_exit']==0 and l['timeout'] is False
  assert rec['outcome']=='SAFE_YIELD' and rec['reason']=='effect_unavailable' and rec['pending_effect']['action']=='enter' and [x['action'] for x in rec['transitions']]==['enter'] and rec['transitions'][0]['release_verified']
  assert method['task_success'] is None and method['replay_allowed'] is False and r['recovery']==q and q['original_replay_allowed'] is False and q['entry_replayed'] is False and q['max_attempts']==1
  assert q['case']==mode and q['cue']==expected_cue and q['new_observation_sequence']>rec['observations'][-1]['sequence'] and q['recovery_ended_ns']<=q['recovery_deadline_ns']
  art=q['observation']['native']['artifact'];data=z.read(f"{tag}/output/"+art['path'].removeprefix('/out/'));assert len(data)==art['bytes'] and hashlib.sha256(data).hexdigest()==art['sha256'];image=Image.open(BytesIO(data)).convert('RGB')
  assert ocr['cue']==expected_cue and ocr['sequence']==q['new_observation_sequence'] and ocr['artifact_sha256']==art['sha256']
  assert ocr['command'][ocr['command'].index('--psm')+1]=='11'  # legacy field, explicitly superseded by runner trace
  expected_count=1 if mode=='slow_child' else 2;assert len(attempts)==len(ocr['crop_attempts'])==expected_count
  for attempt,crop,box in zip(attempts,ocr['crop_attempts'],((95,144,126,159),(95,161,126,176))):
   assert attempt['command']==(['python3','/in/slow_ocr.py']+command[1:] if mode=='slow_child' else command) and attempt['capture_output'] is True and attempt['check'] is False and 0<attempt['timeout_seconds']<=1 and attempt['ended_ns']>=attempt['started_ns']
   payload=crop_png(image,box);assert attempt['input_bytes']==len(payload) and attempt['input_sha256']==crop['sha256']==hashlib.sha256(payload).hexdigest()
   if mode=='slow_child':assert attempt['status']=='timeout' and attempt['error_type']=='TimeoutExpired' and attempt['returncode'] is None
   else:
    assert attempt['status']=='returned' and attempt['returncode']==0 and crop['returncode']==0
    for label,field in [('tsv','stdout_sha256'),('stderr','stderr_sha256')]:assert hashlib.sha256(z.read(f"{tag}/output/recovery-ocr/001-{crop['cell']}.{label}")).hexdigest()==attempt[field]
  if mode=='clear':assert cue(z.read(f'{tag}/output/recovery-ocr/001-A1.tsv'),z.read(f'{tag}/output/recovery-ocr/001-A2.tsv'))=='filled' and q['cue_result']['source_context_verified']
  executions=[n for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1
  e=j(executions[0]);assert e['request']['action']=='enter' and e['result']['status']=='completed' and release(e['result'])
  click=j(f'{tag}/output/click-result.json');assert click['status']=='completed' and release(click)
  mints=[n for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('/mint-recovery_save.json')]
  if mode=='slow_child':
   slow=j(f'{tag}/output/slow-started.json'); obs=q['timeout_observation']; assert obs['child_started'] and obs['pid']==slow['pid'] and not obs['child_present'] and not obs['late_marker'] and obs['observed_ns']-slow['monotonic_ns']>=3000000000 and f'{tag}/output/late-marker' not in z.namelist()
   assert not q['save_attempted'] and not q['save_completed'] and not mints and f'{tag}/output/recovery-save.json' not in z.namelist()
   assert z.read(f'{tag}/output/saved.fods')==z.read(f'{tag}/blank.fods') and r['saved_score']['pass_effect'] is False
  else:
   assert q['save_attempted'] and q['save_completed'] and len(mints)==1
   save=j(f'{tag}/output/recovery-save.json');guard=j(f'{tag}/output/recovery-guard.json')
   assert save['status']=='completed' and release(save) and save['guard_checks'] and all(x['status']=='VALID' and x['eligible'] for x in save['guard_checks'])
   assert guard['events'][0]['event']=='armed' and guard['cue']['cue']=='filled' and guard['cue']['sequence']==q['new_observation_sequence'] and r['saved_score']['pass_effect'] and values(z.read(f'{tag}/output/saved.fods'))==expected
  assert not r['keys_down'] and r['buttons']==0 and r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  req=j(f'{tag}/exchange/request-1.json');resp=j(f'{tag}/exchange/response-1.json');raw=j(f'{tag}/model-call-1/result.json')
  assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and resp['close_returned'] and hashlib.sha256(z.read(f'{tag}/exchange/image-1.png')).hexdigest()==req['image_sha256']==resp['image_sha256']
  assert raw['call_id']==resp['call_id'] and raw['call_id'] not in ids and raw['usage']==resp['usage'] and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['turn_status']=='completed';ids.add(raw['call_id']);assert f'{tag}/exchange/request-2.json' not in z.namelist()
  u=raw['usage'];assert 0<=u['cached_input_tokens']<=u['input_tokens']
  results.append({'allocation':tag,'mode':mode,'cue':q['cue'],'new_save':q['save_completed'],'ocr_attempts':len(attempts),'statuses':[x['status'] for x in attempts],'input_tokens':u['input_tokens'],'output_tokens':u['output_tokens']})
 print(json.dumps({'status':'audited','results':results,'legacy_metadata':'psm11 field retained; recorded runner calls use psm7','trace_scope':'runner-call arguments and hashes, not OS-level tracing'},indent=2))
