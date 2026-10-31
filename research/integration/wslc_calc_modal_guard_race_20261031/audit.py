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
expected=[(0,0,'float','641','641',None),(1,0,'float','283','283',None)]
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
 return 'unknown' if x is None or y is None else ('filled' if (x,y)==('641','283') else 'wrong')
def crop_png(image,box):
 crop=image.crop(box);crop.putdata([(255,255,255) if b>r+30 and b>g+20 else (r,g,b) for r,g,b in crop.getdata()]);crop=crop.convert('L').resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS);crop=ImageOps.expand(crop,border=16,fill=255);buf=BytesIO();crop.save(buf,format='PNG');return buf.getvalue()
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='7e1cdda0373882091860d57138e67a0bc1d7086a34ff8bb610568f167f9bb1cc'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 pre=j('source-precheck.json');assert pre['source_manifest_sha256']==hashlib.sha256(z.read('source-hashes.json')).hexdigest()
 c=j('f12/conditions.json');launch=j('f12/launcher-result.json');r=j('f12/output/result.json');q=j('f12/output/recovery.json');checks=j('f12/output/modal-checks.json');click=j('f12/output/modal-click.json')
 assert c['allocation']=='f12' and c['case']=='race' and launch['exit_code']==0 and not launch['timeout'] and r['recovery']==q
 for n,h in c['candidate'].items():assert hashlib.sha256(z.read('candidate/'+n)).hexdigest()==h,n
 prior=Path(__file__).resolve().parent.parent/'wslc_calc_paste_modal_recovery_20261031'/'public.zip';assert hashlib.sha256(prior.read_bytes()).hexdigest()=='967647425dca0846b652e2b10dd30852fcc139e71f1fa914bd1c3f076c0193a3'
 with ZipFile(prior) as previous:
  pc=json.loads(previous.read('f11/conditions.json'));assert set(pc['candidate'])==set(c['candidate']) and {n for n in c['candidate'] if c['candidate'][n]!=pc['candidate'][n]}=={'runner.py'}
  assert values(previous.read('f11/output/saved.fods'))==expected
 for n in ['calc_ocr_pair_cue_v1.py','calc_ocr_graph_perception_v1.py']:assert z.read('candidate/research/live_control/'+n)==(Path(__file__).resolve().parents[2]/'live_control'/n).read_bytes()
 method=r['method'];assert method['outcome']=='SAFE_YIELD' and method['reason']=='effect_unavailable' and method['completed_transitions']==1 and method['pending_effect']['action']=='enter' and not q['original_replayed']
 assert r['original_close']['release']['verified'] and not r['original_close']['release']['keys_down'] and not r['original_close']['release']['buttons_down'] and q['modal_close']['release']['verified'] and not q['modal_close']['release']['keys_down'] and not q['modal_close']['release']['buttons_down'] and not r['keys_down'] and not r['buttons']
 assert q['modal_reference_match'] and q['modal_title']=='Text Import' and q['modal_attempted'] and not q['modal_completed'] and not q['save_attempted'] and not q['save_completed']
 assert click['status']=='refused' and click['input_dispatched'] is False and len(checks)==1 and checks[0]['stage']=='before_admission' and not checks[0]['identity_match'] and not checks[0]['eligible']
 assert f"f12/output/recovery-save.json" not in z.namelist() and not any(n.endswith('/mint-recovery_save.json') for n in z.namelist()) and z.read('f12/output/saved.fods')==z.read('candidate/blank.fods') and values(z.read('f12/output/saved.fods'))==[]
 ex=[j(n) for n in z.namelist() if n.startswith('f12/output/owner/') and n.endswith('-execution.json')];assert len(ex)==1 and ex[0]['request']['action']=='enter' and ex[0]['result']['status']=='completed' and release(ex[0]['result'])
 assert len([n for n in z.namelist() if n.startswith('f12/output/modal-owner/') and n.endswith('/mint-import_ok.json')])==1
 images={hashlib.sha256(z.read(n)).hexdigest():z.read(n) for n in z.namelist() if n.startswith('f12/output/modal-owner/') and n.endswith('.png')};a=q['modal_observation']['native']['artifact']['sha256'];b=checks[0]['artifact_sha256'];assert a in images and b in images and a!=b
 ref=Image.open(BytesIO(z.read('candidate/modal-reference.png'))).convert('RGB');before=Image.open(BytesIO(images[a])).convert('RGB');after=Image.open(BytesIO(images[b])).convert('RGB');boxes=((575,132,705,153),(411,478,491,515),(408,285,719,432),(791,628,875,655));assert all(ref.crop(box).tobytes()==before.crop(box).tobytes() for box in boxes);assert before.crop(boxes[1]).tobytes()!=after.crop(boxes[1]).tobytes() and all(before.crop(boxes[i]).tobytes()==after.crop(boxes[i]).tobytes() for i in (0,2,3))
 from PIL import ImageChops
 assert ImageChops.difference(before,after).getbbox()==(420,485,428,493)
 obs=[j(n) for n in z.namelist() if n.startswith('f12/output/modal-owner/') and '/observation-' in n and n.endswith('.json')];guard=next(x for x in obs if x['sequence']==checks[0]['sequence']);assert guard['pointer_binding']==q['modal_observation']['pointer_binding'] and guard['native']['artifact']['sha256']==b
 print(json.dumps({'status':'audited','initial_modal':'matched','changed_after_mint':True,'click':'refused before input','saved_file':'unchanged blank','neutral_release':True},indent=2))
