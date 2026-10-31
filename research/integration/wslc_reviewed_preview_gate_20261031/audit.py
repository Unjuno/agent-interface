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
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='fba1733d6900cb2b845bd537eb2c3b64cee77031b6d61e1f6e41e07b227d7db8'
boxes=((575,132,705,153),(411,478,491,515),(408,285,719,432),(791,628,875,655))
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 manifest=j('manifest.json');assert set(z.namelist())==set(manifest['files'])|{'manifest.json'}
 for n,h in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 pre=j('source-precheck.json');assert pre['source_manifest_sha256']==hashlib.sha256(z.read('source-hashes.json')).hexdigest()
 c0=j('f17/conditions.json');c1=j('f18/conditions.json');assert c0['candidate']==c1['candidate'] and c0['order']==c1['order']==['f17:blocked','f18:match']
 for n,h in c0['candidate'].items():assert hashlib.sha256(z.read('candidate/'+n)).hexdigest()==h,n
 assert hashlib.sha256(z.read('candidate/modal-reference.png')).hexdigest()=='809756275baaefdf78e0da879abb6cb150a707765b4209d1f282712488b8585e'
 for name in ('calc_ocr_graph_perception_v1.py','calc_ocr_pair_cue_v1.py','reviewed_modal_guard_v1.py','reviewed_preview_gate_v1.py','test_reviewed_preview_gate_v1.py'):assert z.read('candidate/research/live_control/'+name).replace(b'\r\n',b'\n')==(Path(__file__).resolve().parents[2]/'live_control'/name).read_bytes().replace(b'\r\n',b'\n')
 reference=Image.open(BytesIO(z.read('candidate/modal-reference.png'))).convert('RGB');rows=[]
 def artifact(tag,native):
  a=native['native']['artifact'];payload=z.read(tag+'/output/'+a['path'].removeprefix('/out/'));assert len(payload)==a['bytes'] and hashlib.sha256(payload).hexdigest()==a['sha256'];return Image.open(BytesIO(payload)).convert('RGB')
 for tag,case in [('f17','blocked'),('f18','match')]:
  c=j(f'{tag}/conditions.json');launch=j(f'{tag}/launcher-result.json');r=j(f'{tag}/output/result.json');q=j(f'{tag}/output/recovery.json');assert c['allocation']==tag and c['case']==case and launch['exit_code']==0 and not launch['timeout'] and r['recovery']==q
  method=r['method'];assert method['outcome']=='SAFE_YIELD' and method['reason']=='effect_unavailable' and method['completed_transitions']==1 and method['pending_effect']['action']=='enter' and not q['original_replayed']
  assert r['original_close']['release']['verified'] and not r['original_close']['release']['keys_down'] and not r['original_close']['release']['buttons_down'] and q['modal_close']['release']['verified'] and not q['modal_close']['release']['keys_down'] and not q['modal_close']['release']['buttons_down'] and not r['keys_down'] and not r['buttons']
  assert r['original_close']['session_id']!=q['modal_close']['session_id'];assert q['modal_title']=='Text Import';modal=q['modal_observation'];assert modal['pointer_binding']['focus']==modal['pointer_binding']['surface']==q['modal_id'];image=artifact(tag,modal)
  assert all(reference.crop(boxes[i]).tobytes()==image.crop(boxes[i]).tobytes() for i in (0,2,3))
  assert reference.crop(boxes[1]).tobytes()!=image.crop(boxes[1]).tobytes()
  preview=j(f'{tag}/output/preview.json');assert preview['sequence']==modal['sequence'] and preview['artifact_sha256']==modal['native']['artifact']['sha256'] and len(preview['gate_result']['attempts'])==2
  assert preview['expected']==(['330','517'] if case=='blocked' else ['329','517']) and preview['gate_result']['status']==('wrong' if case=='blocked' else 'armed')
  for index,(item,box) in enumerate(zip(preview['gate_result']['attempts'],((434,496,454,506),(434,509,454,519)))):
   assert item['index']==index and item['box']==list(box) and item['command']==['tesseract','stdin','stdout','--psm','7','-c','tessedit_char_whitelist=0123456789','tsv'] and 0<item['timeout_seconds']<=1 and hashlib.sha256(z.read(f"{tag}/output/preview-{('A1','A2')[index]}.stderr")).hexdigest()==item['stderr_sha256']
   crop=image.crop(box).convert('L').resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS);crop=ImageOps.expand(crop,border=16,fill=255);buf=BytesIO();crop.save(buf,format='PNG');assert hashlib.sha256(buf.getvalue()).hexdigest()==item['input_sha256'] and item['returncode']==0 and hashlib.sha256(z.read(f"{tag}/output/preview-{('A1','A2')[index]}.tsv")).hexdigest()==item['stdout_sha256']
  assert cue(z.read(f'{tag}/output/preview-A1.tsv'),z.read(f'{tag}/output/preview-A2.tsv'))=='filled'
  ex=[j(n) for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('-execution.json')];assert len(ex)==1 and ex[0]['request']['action']=='enter' and ex[0]['result']['status']=='completed' and ex[0]['result']['execution']['emissions']==4 and release(ex[0]['result'])
  if case=='blocked':
   assert not q['modal_reference_match'] and not q['modal_attempted'] and not q['modal_completed'] and not q['save_attempted'] and not q['save_completed']
   assert f'{tag}/output/modal-click.json' not in z.namelist() and f'{tag}/output/recovery-save.json' not in z.namelist() and z.read(f'{tag}/output/saved.fods')==z.read('candidate/blank.fods') and values(z.read(f'{tag}/output/saved.fods'))==[]
  else:
   assert q['modal_reference_match'] and q['modal_attempted'] and q['modal_completed'] and q['save_attempted'] and q['save_completed'] and q['fresh_predicates']['cells_match'] is True
   click=j(f'{tag}/output/modal-click.json');save=j(f'{tag}/output/recovery-save.json');guard=j(f'{tag}/output/save-guard.json');extra=j(f'{tag}/output/modal-checks.json');assert len(extra)==4 and all(x['identity_match'] and x['eligible'] for x in extra)
   for action in (click,save):assert action['status']=='completed' and release(action) and action['guard_checks'] and all(x['status']=='VALID' and x['eligible'] for x in action['guard_checks'])
   assert {x['stage'] for x in click['guard_checks']}=={'before_admission','before_focus','before_move','before_press'} and all(x['point']==[832,640] for x in click['guard_checks'])
   observations=[j(n) for n in z.namelist() if n.startswith(f'{tag}/output/modal-owner/') and '/observation-' in n and n.endswith('.json')];obs_by_seq={x['sequence']:x for x in observations}
   for check in click['guard_checks']:
    current=obs_by_seq[check['observation_sequence']];assert current['pointer_binding']==modal['pointer_binding'];screen=artifact(tag,current);assert all(image.crop(box).tobytes()==screen.crop(box).tobytes() for box in boxes)
   fresh=q['fresh_observation'];assert q['fresh_close']['session_id'] not in {r['original_close']['session_id'],q['modal_close']['session_id']} and q['fresh_close']['release']['verified'] and not q['fresh_close']['release']['keys_down'] and not q['fresh_close']['release']['buttons_down']
   screen=artifact(tag,fresh);ocr=j(f'{tag}/output/ocr.json');actual=[x for x in ocr if 'cell' in x];assert len(actual)==2 and [x['cell'] for x in actual]==['A1','A2'] and all(x['sequence']==fresh['sequence'] and x['returncode']==0 for x in actual)
   for item,box,index in zip(actual,((95,144,126,159),(95,161,126,176)),(6,7)):
    payload=crop_png(screen,box);assert hashlib.sha256(payload).hexdigest()==item['input_sha256'];assert hashlib.sha256(z.read(f'{tag}/output/ocr-{index:03d}.tsv')).hexdigest()==item['stdout_sha256']
   assert cue(z.read(f'{tag}/output/ocr-006.tsv'),z.read(f'{tag}/output/ocr-007.tsv'))=='filled' and guard['events'][0]['event']=='armed' and guard['cue']['sequence']==fresh['sequence'] and guard['cue']['artifact_sha256']==fresh['native']['artifact']['sha256']
   assert values(z.read(f'{tag}/output/saved.fods'))==expected and r['saved_score']['pass_effect']
  rows.append({'allocation':tag,'case':case,'original':'SAFE_YIELD','modal_click':q['modal_completed'],'guarded_save':q['save_completed'],'independent_saved':values(z.read(f'{tag}/output/saved.fods')),'neutral_release':True})
 print(json.dumps({'status':'audited','results':rows},indent=2))
