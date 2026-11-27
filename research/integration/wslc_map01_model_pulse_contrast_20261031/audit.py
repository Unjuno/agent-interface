"""Verify the public full/crop post-cancellation comparison; Pillow required."""
import hashlib, io, json, zipfile
from pathlib import Path
from PIL import Image, ImageChops
with zipfile.ZipFile(Path(__file__).with_name('public.zip')) as z:
 def raw(n):return z.read(n)
 def j(n):return json.loads(raw(n).decode('utf-8-sig'))
 summaries=[]
 for name,arm in (('ae01','full'),('ae02','full')):
  c=j(name+'/conditions.json');r=j(name+'/output/result.json')
  assert c['arm']==arm and c['order']==['ae01:500ms','ae02:1000ms']
  for n,d in c['hashes'].items():assert hashlib.sha256(raw(n)).hexdigest()==d
  for n,d in c['adapter_hashes'].items():assert hashlib.sha256(raw('adapter/'+n)).hexdigest()==d
  assert r['status']=='completed' and r['model_calls']==1 and r['task_success'] is None and r['keys_down_after']==[]
  mon=r['cancel_monitor'];rel=r['cancel_result']['execution']['releases'][-1]
  assert mon['held_observed'] and mon['response']['status']=='cancel_requested'
  assert r['cancel_result']['status']=='execution_failed' and rel['verified'] and not rel['keys_down'] and not rel['buttons_down']
  review=j(name+'/output/review.json');stale=j(name+'/output/stale.json')
  assert review['status']=='reviewed' and review['binding_revision']>review['previous_binding_revision']
  assert mon['held_ns']<=mon['request_ns']<=rel['monotonic_ns']<=review['started_ns']
  assert stale['status']=='refused' and stale['input_dispatched'] is False
  req,done=j(name+'/exchange/request-1.json'),j(name+'/exchange/done-1.json')
  full=raw(name+'/exchange/image-1.png');source_digest=hashlib.sha256(full).hexdigest()
  assert req['image_sha256']==done['image_sha256']==source_digest and r['model_source']['image_sha256']==source_digest
  assert r['model_source']['geometry']==[320,272,640,480] and done==r['model_response'] and done['submitted_arm']==arm
  model_png=raw(name+'/exchange/model-image-1.png') if arm=='crop' else full
  assert hashlib.sha256(model_png).hexdigest()==done['submitted_image_sha256']
  if arm=='crop':
   expected=Image.open(io.BytesIO(full)).convert('RGB').crop((320,272,960,752));actual=Image.open(io.BytesIO(model_png)).convert('RGB')
   assert ImageChops.difference(expected,actual).getbbox() is None
   assert done['grounding']['target_x']==done['model_grounding']['target_x']+320 and done['grounding']['target_y']==done['model_grounding']['target_y']+272
  else:assert done['grounding']==done['model_grounding']
  policy=done['grounding'];assert policy['action']=='fire'
  px,py=policy['target_x'],policy['target_y'];gate=r['gate'];assert gate['eligible'] and gate['binding_equal'] and gate['center'] and gate['bounds']
  def obs(seq):
   matches=[n for n in z.namelist() if n.startswith(name+'/output/') and n.endswith('/observation-%d.json'%seq)];assert len(matches)==1;return j(matches[0])
  a,b=obs(gate['source_sequence']),obs(gate['current_sequence']);assert a['native']['artifact']['sha256']==source_digest and a['pointer_binding']==b['pointer_binding']
  def img(o):
   basename=o['native']['artifact']['path'].split('/')[-1];matches=[n for n in z.namelist() if n.startswith(name+'/output/') and n.endswith('/images/'+basename)];assert len(matches)==1;data=raw(matches[0]);assert hashlib.sha256(data).hexdigest()==o['native']['artifact']['sha256'];return Image.open(io.BytesIO(data)).convert('RGB')
  old=img(a).crop((px-4,py-4,px+4,py+4)).tobytes();new=img(b).crop((px-4,py-4,px+4,py+4)).tobytes();diff=sum(abs(x-y) for x,y in zip(old,new))/len(old);colors=len(set(tuple(old[i:i+3]) for i in range(0,len(old),3)));assert diff==gate['difference'] and colors==gate['colors'] and diff<=32 and colors>=2
  checks=r['model_guard_checks'];assert [x['stage'] for x in checks]==['before_admission','before_focus','before_key_press:f'] and all(x['eligible'] and x['difference']<=32 for x in checks)
  action=j(name+'/output/model-action.json');assert action==r['model_action'] and action['status']=='completed' and action['admission']=='accepted'
  control=r['duration_control'];assert control['model_requested_ms']==policy['duration_ms'] and control['executed_ms']==c['fixed_duration_ms']
  assert action['execution']['waits'][0]['requested_ms']==c['fixed_duration_ms'] and review['ended_ns']<=action['execution']['started_ns']
  releases=action['execution']['releases'];assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
  before=next(x for x in r['samples'] if x['label']=='before_model_action');after=next(x for x in r['samples'] if x['label']=='after_model_action')
  coast=[x for x in r['samples'] if x['label'].startswith('post_action_coast_')];assert len(coast)==8 and [x['label'] for x in coast]==['post_action_coast_%d'%i for i in range(8)]
  expected=0 if name=='ae01' else 1;assert before['kills']==0 and after['kills']==expected and all(x['kills']==expected for x in coast) and r['kill_delta']==expected
  assert len(r['actions'])==2 and action['execution']['releases'][-1]['monotonic_ns']<=after['host_ns']<coast[0]['host_ns']<coast[-1]['host_ns']
  assert r['close']['release']['verified'] and j(name+'/exchange/closed.json')['closed'] is True
  summaries.append({'allocation':name,'arm':arm,'model_requested_ms':policy['duration_ms'],'executed_ms':c['fixed_duration_ms'],'model_usage':done['usage'],'model_seconds':done['runner_ns']/1e9,'kill_before_immediate_final':[before['kills'],after['kills'],coast[-1]['kills']],'coast_ms':(coast[-1]['host_ns']-after['host_ns'])/1e6,'final_keys':r['keys_down_after']})
 assert summaries[0]['model_usage']['input_tokens']==12499 and summaries[1]['model_usage']['input_tokens']==12499
 print(json.dumps({'status':'audited','arms':summaries},indent=2))
