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
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='23c63bbe28983e89a47ddc5394edf31d5f31b65f2409febcf0c85e210df7bd3e'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 manifest=j('manifest.json');assert set(z.namelist())==set(manifest['files'])|{'manifest.json'}
 for n,h in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not any(v['input_mismatches'].values()) and v['list_exit']==0 and not v['present']
 pre=j('source-precheck.json');assert pre['main_commit']=='9ad6c0099c44f6be901e7310866b8ea4b70a46a7' and pre['source_manifest_sha256']==hashlib.sha256(z.read('source-hashes.json')).hexdigest()
 c0=j('e10/conditions.json');c1=j('e11/conditions.json');assert c0['input_sha256']==c1['input_sha256'];ids=set();rows=[]
 command=['tesseract','stdin','stdout','--psm','7','-c','tessedit_char_whitelist=0123456789','tsv']
 for tag,route,count,ocrdir in [('e10','compiled',1,'recovery-ocr'),('e11','fresh',2,'fresh-ocr')]:
  c=j(f'{tag}/conditions.json');r=j(f'{tag}/output/result.json');launch=j(f'{tag}/launcher-result.json');ocr=j(f'{tag}/output/{ocrdir}/001.json');attempts=j(f'{tag}/output/ocr-attempts.json')
  assert c['allocation']==tag and c['route']==route and c['order']==['e10:compiled','e11:fresh'] and c['base_main']=='8a8fa67150ac8940a17207804723879d39275688'
  for n,h in c['input_sha256'].items():assert hashlib.sha256(z.read(f'{tag}/{n}')).hexdigest()==h,n
  assert launch['container_exit']==launch['host_exit']==0 and not launch['timeout'] and launch['elapsed_seconds']>0
  assert r['route']==route and values(z.read(f'{tag}/output/saved.fods'))==expected and r['saved_score']['pass_effect']
  assert not r['keys_down'] and r['buttons']==0 and r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  assert release(j(f'{tag}/output/click-result.json')) and ocr['cue']=='filled' and ocr['source_context_verified'] and ocr['command'][ocr['command'].index('--psm')+1]=='11'
  candidates=[n for n in z.namelist() if n.startswith(f'{tag}/output/') and n.endswith('.png') and hashlib.sha256(z.read(n)).hexdigest()==ocr['artifact_sha256']];assert candidates
  image=Image.open(BytesIO(z.read(candidates[0]))).convert('RGB');assert len(attempts)==len(ocr['crop_attempts'])==2
  for attempt,crop,box in zip(attempts,ocr['crop_attempts'],((95,144,126,159),(95,161,126,176))):
   assert attempt['command']==command and attempt['status']=='returned' and attempt['returncode']==0 and attempt['capture_output'] and not attempt['check'] and 0<attempt['timeout_seconds']<=1
   payload=crop_png(image,box);assert attempt['input_bytes']==len(payload) and attempt['input_sha256']==crop['sha256']==hashlib.sha256(payload).hexdigest()
   for suffix,field in [('tsv','stdout_sha256'),('stderr','stderr_sha256')]:assert hashlib.sha256(z.read(f"{tag}/output/{ocrdir}/001-{crop['cell']}.{suffix}")).hexdigest()==attempt[field]
  assert cue(z.read(f'{tag}/output/{ocrdir}/001-A1.tsv'),z.read(f'{tag}/output/{ocrdir}/001-A2.tsv'))=='filled'
  if route=='compiled':
   m=r['method'];rec=m['method_receipt'];q=j(f'{tag}/output/recovery.json');assert rec['outcome']=='SAFE_YIELD' and rec['reason']=='effect_unavailable' and rec['pending_effect']['action']=='enter' and [x['action'] for x in rec['transitions']]==['enter'] and rec['transitions'][0]['release_verified']
   assert m['task_success'] is None and not m['replay_allowed'] and not q['entry_replayed'] and q['save_attempted'] and q['save_completed'] and q['recovery_ended_ns']<=q['recovery_deadline_ns'] and q['new_observation_sequence']==ocr['sequence']
   save=j(f'{tag}/output/recovery-save.json');guard=j(f'{tag}/output/recovery-guard.json')
   executions=[n for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1;ex=j(executions[0]);assert ex['request']['action']=='enter' and ex['result']['status']=='completed' and release(ex['result'])
  else:
   assert r['method']['status']=='completed';entry=j(f'{tag}/output/fresh-entry.json');assert entry['status']=='completed' and release(entry)
   save=j(f'{tag}/output/fresh-save.json');guard=j(f'{tag}/output/fresh-semantic-guard.json')
  mint_name='mint-recovery_save.json' if route=='compiled' else 'mint-fresh_save.json';mints=[n for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('/'+mint_name)];assert len(mints)==1
  assert save['status']=='completed' and release(save) and save['guard_checks'] and all(x['status']=='VALID' and x['eligible'] for x in save['guard_checks'])
  assert guard['events'][0]['event']=='armed' and guard['cue']['cue']=='filled' and guard['cue']['sequence']==ocr['sequence'] and guard['cue']['artifact_sha256']==ocr['artifact_sha256']
  usage=[];thread=None
  for i in range(1,count+1):
   req=j(f'{tag}/exchange/request-{i}.json');resp=j(f'{tag}/exchange/response-{i}.json');raw=j(f'{tag}/model-call-{i}/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and hashlib.sha256(z.read(f'{tag}/exchange/image-{i}.png')).hexdigest()==req['image_sha256']==resp['image_sha256']
   assert raw['call_id']==resp['call_id'] and raw['call_id'] not in ids and raw['usage']==resp['usage'] and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['turn_status']=='completed';ids.add(raw['call_id']);usage.append(raw['usage'])
   if thread is None:thread=raw['thread_id']
   else:assert thread==raw['thread_id']
   assert resp.get('close_returned',False)==(i==count) and 0<=raw['usage']['cached_input_tokens']<=raw['usage']['input_tokens']
  assert f'{tag}/exchange/request-{count+1}.json' not in z.namelist();assert r['task_start_ns']<r['method_start_ns']<r['method_end_ns']<r['task_end_ns']
  rows.append({'allocation':tag,'route':route,'launcher_seconds':launch['elapsed_seconds'],'task_seconds':(r['task_end_ns']-r['task_start_ns'])/1e9,'input_tokens':sum(u['input_tokens'] for u in usage),'cached_input_subset':sum(u['cached_input_tokens'] for u in usage),'output_tokens':sum(u['output_tokens'] for u in usage),'model_calls':count,'ocr_calls':len(attempts)})
 print(json.dumps({'status':'audited','results':rows,'legacy_ocr_command':'psm11 historical metadata; actual recorded runner calls psm7','limitations':'fixed crop and known expected values, old reference only matters to compiled; no full cost or general efficacy'},indent=2))
