"""Audit owned private-Xvfb guard trials, including setup failures."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
import hashlib,json
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='ffc1c6a0ea25b25073fd87ca84d12e5c1219c4bdbbb8fb5ed62c6c0151d3ae48'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty'] and v['not_started']==['f03','f05']
 pre=j('source-precheck.json');assert pre['main_commit']=='9ad6c0099c44f6be901e7310866b8ea4b70a46a7' and pre['source_manifest_sha256']==hashlib.sha256(z.read('source-hashes.json')).hexdigest()
 for tag in ('f02','f03','f04','f05','f06','f07'):
  c=j(f'{tag}/conditions.json');assert c['allocation']==tag
  for n,h in c['candidate'].items():assert hashlib.sha256(z.read(f'{tag}/candidate/{n}')).hexdigest()==h,n
  assert z.read(f'{tag}/candidate/research/live_control/calc_ocr_graph_perception_v1.py')==(Path(__file__).resolve().parents[2]/'live_control/calc_ocr_graph_perception_v1.py').read_bytes()
 for tag in ('f03','f05'):assert f'{tag}/launcher-result.json' not in z.namelist()
 assert j('f02/launcher-result.json')['exit_code']==1 and b'FlatTargetRefused' in z.read('f02/stderr') and not any(n.startswith('f02/output/') and n.endswith('-execution.json') for n in z.namelist())
 f04=j('f04/output/result.json');assert j('f04/launcher-result.json')['exit_code']==1 and b"KeyError: 'release'" in z.read('f04/stderr') and f04['result']['outcome']=='SAFE_YIELD' and not f04['key_events'] and not f04['keys_down'] and not f04['buttons'] and not f04['close']['release_attempted']
 rows=[]
 for tag,case in [('f06','changed'),('f07','unchanged')]:
  c=j(f'{tag}/conditions.json');launch=j(f'{tag}/launcher-result.json');r=j(f'{tag}/output/result.json');assert c['case']==r['case']==case and c['order']==['f06:changed','f07:unchanged'] and launch['exit_code']==0 and not launch['timeout']
  assert r['result']['outcome']=='SAFE_YIELD' and r['close']['status']=='closed' and r['close']['release_attempted'] and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down'] and not r['buttons']
  images={hashlib.sha256(z.read(n)).hexdigest():z.read(n) for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('.png')}
  seen=r['seen'];assert len(seen)>=2 and seen[0]['blank'];assert all(x['image_sha256'] in images for x in seen)
  patches=[Image.open(BytesIO(images[x['image_sha256']])).convert('RGB').crop((24,24,36,36)).tobytes() for x in seen];assert all(x['blank']==(patch==patches[0]) for x,patch in zip(seen,patches))
  deps=[j(n) for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('-input_dependency.json')];execution=[j(n) for n in z.namelist() if n.startswith(f'{tag}/output/owner/') and n.endswith('-execution.json')];assert len(execution)==1 and all('cells_blank' in x['required_predicates'] for x in deps)
  events=r['key_events'];press=[x['keycode'] for x in events if x['type']=='press'];released=[x['keycode'] for x in events if x['type']=='release']
  if case=='changed':
   assert r['change_injected_after_sequence']==[seen[0]['sequence']] and not seen[1]['blank'] and patches[0]!=patches[1] and len(deps)==1 and not deps[0]['eligible'] and deps[0]['predicates']['cells_blank'] is False
   assert execution[0]['result']['status']=='refused' and execution[0]['result']['input_dispatched'] is False and r['result']['completed_transitions']==0 and not press and not released
  else:
   assert not r['change_injected_after_sequence'] and all(x['blank'] for x in seen) and all(x['eligible'] and x['predicates']['cells_blank'] is True for x in deps)
   assert execution[0]['result']['status']=='completed' and execution[0]['result']['execution']['emissions']==6 and r['result']['completed_transitions']==1 and len(press)==3 and press==released
   assert all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in execution[0]['result']['execution']['releases'])
  rows.append({'allocation':tag,'outcome':r['result']['outcome'],'reason':r['result']['reason'],'transitions':r['result']['completed_transitions'],'x_key_presses':len(press),'neutral_release':r['close']['release']['verified']})
 print(json.dumps({'status':'audited','setup_failures':['f02','f04'],'unstarted':['f03','f05'],'results':rows},indent=2))
