"""Audit frozen inputs, image guards, model-directed steering, and scorer observations."""
import hashlib,io,json,zipfile
from pathlib import Path
from PIL import Image
with zipfile.ZipFile(Path(__file__).with_name('public.zip')) as z:
 def raw(n): return z.read(n)
 def j(n): return json.loads(raw(n).decode('utf-8-sig'))
 manifest=j('frozen-manifest.json'); assert all(hashlib.sha256(raw(k)).hexdigest()==v for k,v in manifest.items()); rows=[]
 for arm,mode in [('ak01','wait'),('ak02','steer')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');assert hashlib.sha256(raw('frozen-manifest.json')).hexdigest()==c['manifest_sha256']
  assert c['mode']==r['steer_mode']==mode and r['status']=='completed' and r['task_success'] is None and r['keys_down_after']==[]
  rel=r['close']['release'];assert rel['verified'] and not rel['keys_down'] and not rel['buttons_down'] and j(f'{arm}/exchange/closed.json')['closed']
  mon=r['cancel_monitor'];crel=r['cancel_result']['execution']['releases'][-1];review=j(f'{arm}/output/review.json');stale=j(f'{arm}/output/stale.json')
  assert mon['held_observed'] and mon['response']['status']=='cancel_requested' and crel['verified'] and not crel['keys_down'] and not crel['buttons_down'] and mon['held_ns']<=mon['request_ns']<=crel['monotonic_ns']<=review['started_ns']
  assert review['status']=='reviewed' and stale['status']=='refused' and stale['input_dispatched'] is False
  response=j(f'{arm}/exchange/done-1.json');req=j(f'{arm}/exchange/request-1.json');digest=hashlib.sha256(raw(f'{arm}/exchange/image-1.png')).hexdigest();assert req['image_sha256']==response['image_sha256']==response['submitted_image_sha256']==digest==r['source1_digest'] and response==r['model_responses'][0]
  accepted=j(f'{arm}/exchange/accepted-1.json');pending=j(f'{arm}/exchange/pending-check-1.json');assert accepted==r['turn_accepted'] and pending==r['pending_check'] and pending['no_completion_observed'] and pending['turn_id']==accepted['turn_id']==response['call_id'] and not j(f'{arm}/exchange/overlay-ready.json')['mapped']
  def obs(seq):
   matches=[n for n in z.namelist() if n.startswith(f'{arm}/output/') and n.endswith(f'/observation-{seq}.json')];assert len(matches)==1;return j(matches[0])
  def img(o):
   basename=o['native']['artifact']['path'].split('/')[-1];matches=[n for n in z.namelist() if n.startswith(f'{arm}/output/') and n.endswith('/images/'+basename)];assert len(matches)==1;data=raw(matches[0]);assert hashlib.sha256(data).hexdigest()==o['native']['artifact']['sha256'];return Image.open(io.BytesIO(data)).convert('RGB')
  def patch(im,x,y):return im.crop((x-4,y-4,x+4,y+4)).tobytes()
  def diff(a,b):assert len(a)==len(b) and a;return sum(abs(x-y) for x,y in zip(a,b))/len(a)
  g=r['gate'];a,b=obs(g['source_sequence']),obs(g['current_sequence']);policy=response['grounding'];x,y=policy['target_x'],policy['target_y'];before=patch(img(a),x,y);current=patch(img(b),x,y)
  assert a['native']['artifact']['sha256']==digest and a['pointer_binding']==b['pointer_binding'] and diff(before,current)==g['difference'] and g['eligible'] and g['difference']<=32 and policy['action']=='fire'
  assert r['model_offset_px']==x-640 and abs(r['model_offset_px'])>5
  if mode=='wait':assert r['steering']=={'status':'withheld_control','input_dispatched':False}
  else:
   key='d' if r['model_offset_px']>0 else 'a';assert r['steer_key']==key;action=j(f'{arm}/output/steer-action.json');assert action==r['steering'] and action['status']=='completed' and action['execution']['waits'][0]['requested_ms']==50
   assert all(v['verified'] and not v['keys_down'] and not v['buttons_down'] for v in action['execution']['releases'])
   checks=r['steering_guard_checks'];assert [v['stage'] for v in checks]==['before_admission','before_focus','before_key_press:'+key]
   for check in checks:
    o=obs(check['sequence']);assert o['pointer_binding']==b['pointer_binding'] and diff(patch(img(o),x,y),current)==check['difference'] and check['eligible'] and check['difference']<=32
  values=[]
  for label in ('steer_before','steer_after','steer_coast'):
   sample=next(v for v in r['samples'] if v['label']==label);enemies=[v for v in r['scorer_labels'][label] if v['name']=='Zombieman'];assert len(enemies)==1;enemy=enemies[0];raw(f'{arm}/output/scene-{label}.png')
   values.append({'angle':sample['angle'],'enemy_x_center':enemy['x']+enemy['width']/2,'ammo':sample['ammo'],'kills':sample['kills']})
  errors=[abs(v['enemy_x_center']-320) for v in values];rows.append({'arm':arm,'mode':mode,'model_target':policy,'scorer_values':values,'absolute_errors_px':errors,'usage':response['usage'],'model_seconds':response['runner_ns']/1e9})
 assert rows[0]['absolute_errors_px']==[16,16,16] and rows[1]['absolute_errors_px']==[16,4,4]
 print(json.dumps({'status':'audited','rows':rows},indent=2))
