"""Audit retained two-arm evidence, including native screenshot patches (Pillow required)."""
import hashlib, io, json, zipfile
from pathlib import Path
from PIL import Image
with zipfile.ZipFile(Path(__file__).with_name('public.zip')) as z:
 def raw(n): return z.read(n)
 def j(n): return json.loads(raw(n).decode('utf-8-sig'))
 reports=[]
 for arm,mode,count in (('ai01','unchanged',1),('ai02','overlay',2)):
  c=j(f'{arm}/conditions.json'); r=j(f'{arm}/output/result.json')
  for n,d in c['hashes'].items(): assert hashlib.sha256(raw(n)).hexdigest()==d
  for n,d in c['adapter_hashes'].items(): assert hashlib.sha256(raw('adapter/'+n)).hexdigest()==d
  assert c['change_mode']==r['change_mode']==mode and r['status']=='completed' and r['task_success'] is None and r['keys_down_after']==[]
  assert len(r['model_responses'])==count and r['replan_required']==(mode=='overlay')
  mon=r['cancel_monitor']; rel=r['cancel_result']['execution']['releases'][-1]; review=j(f'{arm}/output/review.json'); stale=j(f'{arm}/output/stale.json')
  assert mon['held_observed'] and mon['response']['status']=='cancel_requested' and r['cancel_result']['status']=='execution_failed'
  assert rel['verified'] and not rel['keys_down'] and not rel['buttons_down'] and mon['held_ns']<=mon['request_ns']<=rel['monotonic_ns']<=review['started_ns']
  assert review['status']=='reviewed' and stale['status']=='refused' and not stale['input_dispatched']
  acc=j(f'{arm}/exchange/accepted-1.json'); pending=j(f'{arm}/exchange/pending-check-1.json'); ack=j(f'{arm}/exchange/overlay-ready.json')
  assert acc==r['turn_accepted'] and pending==r['pending_check'] and acc['accepted'] and ack['mapped']==(mode=='overlay')
  assert pending['no_completion_observed'] and acc['turn_id']==pending['turn_id']==r['model_responses'][0]['call_id']
  def obs(seq):
   matches=[n for n in z.namelist() if n.startswith(f'{arm}/output/') and n.endswith(f'/observation-{seq}.json')]; assert len(matches)==1; return j(matches[0])
  def img(o):
   name=o['native']['artifact']['path'].split('/')[-1]; matches=[n for n in z.namelist() if n.startswith(f'{arm}/output/') and n.endswith('/images/'+name)]; assert len(matches)==1; data=raw(matches[0]); assert hashlib.sha256(data).hexdigest()==o['native']['artifact']['sha256']; return Image.open(io.BytesIO(data)).convert('RGB')
  def patch(im,x,y): return im.crop((x-4,y-4,x+4,y+4)).tobytes()
  def diff(a,b): assert len(a)==len(b) and a; return sum(abs(x-y) for x,y in zip(a,b))/len(a)
  for i in range(1,count+1):
   gate=r['first_gate' if i==1 else 'fresh_gate']; req=j(f'{arm}/exchange/request-{i}.json'); done=j(f'{arm}/exchange/done-{i}.json'); data=raw(f'{arm}/exchange/image-{i}.png'); digest=hashlib.sha256(data).hexdigest()
   assert req['image_sha256']==done['image_sha256']==done['submitted_image_sha256']==digest==r[f'source{i}_digest']
   assert done==r['model_responses'][i-1] and done['grounding']['action']=='fire'
   a,b=obs(gate['source_sequence']),obs(gate['current_sequence']); assert a['native']['artifact']['sha256']==digest and a['pointer_binding']==b['pointer_binding']
   policy=done['grounding']; x,y=policy['target_x'],policy['target_y']; before=patch(img(a),x,y); current=patch(img(b),x,y)
   assert diff(before,current)==gate['difference'] and gate['binding_equal'] and gate['bounds'] and gate['center']
   if mode=='overlay' and i==1:
    review2=j(f'{arm}/output/replan-review.json'); assert r['first_action']=={'status':'withheld','input_dispatched':False} and not gate['eligible'] and gate['difference']>32
    assert r['turn_accepted_seen_ns']<=r['overlay']['mapped_ns'] and a['capture_ns']<=r['overlay']['mapped_ns']<=b['capture_ns']<=r['overlay_removed_ns']<=review2['started_ns'] and review2['status']=='reviewed'
   else:
    assert gate['eligible'] and gate['difference']<=32
    if i==2: assert review2['ended_ns']<=a['capture_ns']
    checks=r['model_guard_checks']; assert [k['stage'] for k in checks]==['before_admission','before_focus','before_key_press:f']
    for check in checks:
     o=obs(check['sequence']); assert o['pointer_binding']==b['pointer_binding'] and diff(patch(img(o),x,y),current)==check['difference'] and check['eligible'] and check['difference']<=32
  action=j(f'{arm}/output/model-action.json'); assert action==r['model_action'] and action['status']=='completed' and action['admission']=='accepted'
  assert action['execution']['waits'][0]['requested_ms']==r['model_responses'][-1]['grounding']['duration_ms']
  assert all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in action['execution']['releases'])
  before=next(x for x in r['samples'] if x['label']=='before_model_action'); after=next(x for x in r['samples'] if x['label']=='after_model_action'); coast=[x for x in r['samples'] if x['label'].startswith('post_action_coast_')]
  assert len(coast)==8 and before['ammo']==50 and coast[-1]['ammo']==48 and before['kills']==after['kills']==coast[-1]['kills']==0
  assert action['execution']['releases'][-1]['monotonic_ns']<=after['host_ns']<coast[0]['host_ns']<coast[-1]['host_ns']
  assert r['close']['release']['verified'] and not r['close']['release']['keys_down'] and j(f'{arm}/exchange/closed.json')['closed'] is True
  reports.append({'arm':arm,'mode':mode,'first_difference':r['first_gate']['difference'],'calls':count,'decision_seconds':(r['decision_ready_ns']-r['decision_started_ns'])/1e9,'call_seconds':[v['runner_ns']/1e9 for v in r['model_responses']],'usage':[v['usage'] for v in r['model_responses']],'ammo':[before['ammo'],after['ammo'],coast[-1]['ammo']],'kills':[before['kills'],after['kills'],coast[-1]['kills']],'keys_down_after':r['keys_down_after']})
 print(json.dumps({'status':'audited','arms':reports},indent=2))
