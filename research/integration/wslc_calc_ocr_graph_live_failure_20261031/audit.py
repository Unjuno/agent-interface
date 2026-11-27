"""Audit retained real-Calc partial-entry regression."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageOps
import hashlib,json
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='9bc62e5b2f10be27f7085ead303361f6fd5f92c94074f7030cbc5c0ea26a3db1'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 manifest=j('manifest.json');assert set(z.namelist())==set(manifest['files'])|{'manifest.json'}
 for n,h in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 pre=j('source-precheck.json');assert pre['source_manifest_sha256']==hashlib.sha256(z.read('source-hashes.json')).hexdigest()
 c=j('f08/conditions.json');launch=j('f08/launcher-result.json');r=j('f08/output/result.json');trace=j('f08/output/trace.json');ocr=j('f08/output/ocr.json')
 assert c['allocation']=='f08' and launch['exit_code']==0 and not launch['timeout']
 for n,h in c['candidate'].items():assert hashlib.sha256(z.read('candidate/'+n)).hexdigest()==h,n
 for n in ['calc_ocr_pair_cue_v1.py','calc_ocr_graph_perception_v1.py']:assert z.read('candidate/research/live_control/'+n)==(Path(__file__).resolve().parents[2]/'live_control'/n).read_bytes()
 method=r['method'];assert method['outcome']=='SAFE_YIELD' and method['reason']=='execution_failed' and method['completed_transitions']==0 and method['pending_effect'] is None
 assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down'] and not r['buttons']
 assert z.read('f08/output/saved.fods')==z.read('candidate/blank.fods') and not r['saved_score']['pass_effect'] and not r['saved_score']['populated']
 deps=[j(n) for n in z.namelist() if n.startswith('f08/output/owner/') and n.endswith('-input_dependency.json')];execs=[j(n) for n in z.namelist() if n.startswith('f08/output/owner/') and n.endswith('-execution.json')];assert len(execs)==1
 ex=execs[0];assert ex['request']['action']=='enter' and ex['result']['status']=='execution_failed' and ex['result']['execution']['emissions']==4 and ex['result']['execution']['failed_op']==5 and 'partial input' in ex['result']['execution']['failed_op_effect']
 assert ex['result']['execution']['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in ex['result']['execution']['releases'])
 refusal=[x for x in deps if x['stage']=='before_key_press:1'];assert len(refusal)==1 and not refusal[0]['eligible'] and refusal[0]['predicates']['cells_blank'] is False and refusal[0]['predicates']['cells_match']=='unknown'
 assert any(x['stage']=='before_key_press:6' and x['eligible'] for x in deps) and any(x['stage']=='before_key_press:4' and x['eligible'] for x in deps)
 images={hashlib.sha256(z.read(n)).hexdigest():z.read(n) for n in z.namelist() if n.startswith('f08/output/owner/') and n.endswith('.png')};assert all(x['artifact_sha256'] in images for x in trace)
 initial=Image.open(BytesIO(images[trace[0]['artifact_sha256']])).convert('RGB');changed=[x for x in trace if x['sequence']==refusal[0]['observation_sequence']];assert len(changed)==1 and changed[0]['blank'] is False and trace[0]['blank'] is True
 image=Image.open(BytesIO(images[changed[0]['artifact_sha256']])).convert('RGB');assert any(initial.crop(box).tobytes()!=image.crop(box).tobytes() for box in ((37,143,126,159),(37,159,126,176)))
 actual=[x for x in ocr if 'cell' in x];assert len(actual)==2 and [x['cell'] for x in actual]==['A1','A2'] and all(x['sequence']==changed[0]['sequence'] and x['returncode']==0 for x in actual)
 for item,box,index in zip(actual,((95,144,126,159),(95,161,126,176)),(5,6)):
  crop=image.crop(box);crop.putdata([(255,255,255) if b>r+30 and b>g+20 else (r,g,b) for r,g,b in crop.getdata()]);crop=crop.convert('L').resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS);crop=ImageOps.expand(crop,border=16,fill=255);buf=BytesIO();crop.save(buf,format='PNG');assert hashlib.sha256(buf.getvalue()).hexdigest()==item['input_sha256'];assert hashlib.sha256(z.read(f'f08/output/ocr-{index:03d}.tsv')).hexdigest()==item['stdout_sha256']
 print(json.dumps({'status':'audited','outcome':method['outcome'],'reason':method['reason'],'input_emissions':4,'completed_transitions':0,'guard_refused':'before_key_press:1','neutral_release':True,'saved_file':'unchanged blank'},indent=2))
