"""Verify the retained stale-image and fresh-replan evidence; Pillow required."""
import hashlib, io, json, zipfile
from pathlib import Path
from PIL import Image
with zipfile.ZipFile(Path(__file__).with_name('public.zip')) as z:
 def raw(n):return z.read(n)
 def j(n):return json.loads(raw(n).decode('utf-8-sig'))
 c=j('ah01/conditions.json');r=j('ah01/output/result.json')
 for n,d in c['hashes'].items():assert hashlib.sha256(raw(n)).hexdigest()==d
 for n,d in c['adapter_hashes'].items():assert hashlib.sha256(raw('adapter/'+n)).hexdigest()==d
 assert r['status']=='completed' and r['model_calls']==2 and r['task_success'] is None and r['keys_down_after']==[]
 mon=r['cancel_monitor'];rel=r['cancel_result']['execution']['releases'][-1]
 assert mon['held_observed'] and mon['response']['status']=='cancel_requested' and r['cancel_result']['status']=='execution_failed'
 assert rel['verified'] and not rel['keys_down'] and not rel['buttons_down']
 review=j('ah01/output/review.json');stale=j('ah01/output/stale.json');review2=j('ah01/output/replan-review.json')
 assert review['status']=='reviewed' and review2['status']=='reviewed'
 assert mon['held_ns']<=mon['request_ns']<=rel['monotonic_ns']<=review['started_ns']
 assert stale['status']=='refused' and stale['input_dispatched'] is False
 assert review2['binding_revision']>review2['previous_binding_revision']>=review['binding_revision']
 assert r['first_action']=={'status':'withheld','input_dispatched':False}
 assert len(r['model_responses'])==2
 accepted=j('ah01/exchange/accepted-1.json');pending=j('ah01/exchange/pending-check-1.json');overlay_ready=j('ah01/exchange/overlay-ready.json')
 assert accepted==r['turn_accepted'] and pending==r['pending_check'] and accepted['accepted'] and overlay_ready['mapped']
 assert pending['no_completion_observed'] and accepted['turn_id']==pending['turn_id']==r['model_responses'][0]['call_id']
 assert r['turn_accepted_seen_ns']<=r['overlay']['mapped_ns']
 def obs(seq):
  matches=[n for n in z.namelist() if n.startswith('ah01/output/') and n.endswith('/observation-%d.json'%seq)];assert len(matches)==1;return j(matches[0])
 def img(o):
  basename=o['native']['artifact']['path'].split('/')[-1];matches=[n for n in z.namelist() if n.startswith('ah01/output/') and n.endswith('/images/'+basename)];assert len(matches)==1;data=raw(matches[0]);assert hashlib.sha256(data).hexdigest()==o['native']['artifact']['sha256'];return Image.open(io.BytesIO(data)).convert('RGB')
 def patch(im,px,py):return im.crop((px-4,py-4,px+4,py+4)).tobytes()
 def difference(a,b):assert len(a)==len(b) and a;return sum(abs(x-y) for x,y in zip(a,b))/len(a)
 outputs=[]
 for i,key in ((1,'stale_gate'),(2,'fresh_gate')):
  gate=r[key];req=j('ah01/exchange/request-%d.json'%i);done=j('ah01/exchange/done-%d.json'%i);data=raw('ah01/exchange/image-%d.png'%i);digest=hashlib.sha256(data).hexdigest()
  assert req['image_sha256']==done['image_sha256']==done['submitted_image_sha256']==digest==r['source%d_digest'%i]
  assert done==r['model_responses'][i-1] and done['submitted_arm']=='full' and done['grounding']['action']=='fire'
  a,b=obs(gate['source_sequence']),obs(gate['current_sequence']);assert a['native']['artifact']['sha256']==digest and a['pointer_binding']==b['pointer_binding']
  policy=done['grounding'];px,py=policy['target_x'],policy['target_y'];before=patch(img(a),px,py);current=patch(img(b),px,py)
  assert difference(before,current)==gate['difference'] and gate['binding_equal'] and gate['bounds'] and gate['center']
  if i==1:
   assert gate['difference']>32 and not gate['eligible']
   assert a['capture_ns']<=r['overlay']['mapped_ns']<=b['capture_ns']<=r['overlay_removed_ns']<=review2['started_ns']
  else:
   assert gate['difference']<=32 and gate['eligible'] and review2['ended_ns']<=a['capture_ns']
   checks=r['model_guard_checks'];assert [x['stage'] for x in checks]==['before_admission','before_focus','before_key_press:f']
   for check in checks:
    o=obs(check['sequence']);assert o['pointer_binding']==b['pointer_binding']
    assert difference(patch(img(o),px,py),current)==check['difference'] and check['eligible'] and check['difference']<=32
  outputs.append({'call':i,'gate_difference':gate['difference'],'eligible':gate['eligible'],'usage':done['usage'],'call_seconds':done['runner_ns']/1e9})
 action=j('ah01/output/model-action.json');assert action==r['model_action'] and action['status']=='completed' and action['admission']=='accepted'
 assert action['execution']['waits'][0]['requested_ms']==r['model_responses'][1]['grounding']['duration_ms']
 assert action['execution']['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in action['execution']['releases'])
 before=next(x for x in r['samples'] if x['label']=='before_model_action');after=next(x for x in r['samples'] if x['label']=='after_model_action');coast=[x for x in r['samples'] if x['label'].startswith('post_action_coast_')]
 assert len(coast)==8 and before['ammo']==50 and after['ammo']==48 and all(x['ammo']==48 for x in coast)
 assert before['kills']==after['kills']==0 and all(x['kills']==0 for x in coast)
 assert action['execution']['releases'][-1]['monotonic_ns']<=after['host_ns']<coast[0]['host_ns']<coast[-1]['host_ns']
 assert r['close']['release']['verified'] and not r['close']['release']['keys_down'] and j('ah01/exchange/closed.json')['closed'] is True
 print(json.dumps({'status':'audited','calls':outputs,'accepted_turn_no_completion_observed_after_overlay':True,'first_input_dispatched':False,'second_action':action['status'],'ammo':[before['ammo'],after['ammo'],coast[-1]['ammo']],'kills':[before['kills'],after['kills'],coast[-1]['kills']],'coast_ms':(coast[-1]['host_ns']-after['host_ns'])/1e6,'final_keys':r['keys_down_after']},indent=2))
