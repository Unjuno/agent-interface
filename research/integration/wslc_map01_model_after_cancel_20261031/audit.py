"""Audit the public model-after-cancellation evidence; Pillow required."""
import hashlib, io, json, zipfile
from pathlib import Path
from PIL import Image
root=Path(__file__).parent
with zipfile.ZipFile(root/'public.zip') as z:
 def raw(name):return z.read(name)
 def j(name):return json.loads(raw(name).decode('utf-8-sig'))
 c=j('ac02/conditions.json')
 for name,digest in c['hashes'].items():assert hashlib.sha256(raw(name)).hexdigest()==digest
 for name,digest in c['adapter_hashes'].items():assert hashlib.sha256(raw('adapter/'+name)).hexdigest()==digest
 assert j('ac01/exchange/host-error.json')['error']=='AppServerUnsupportedRuntime'
 assert not any(n.startswith('ac01/exchange/request-') for n in z.namelist())
 r=j('ac02/output/result.json');assert r['status']=='completed' and r['model_calls']==1 and r['task_success'] is None
 mon=r['cancel_monitor'];rel=r['cancel_result']['execution']['releases'][-1]
 assert mon['held_observed'] and mon['response']['status']=='cancel_requested'
 assert r['cancel_result']['status']=='execution_failed' and rel['verified'] and not rel['keys_down'] and not rel['buttons_down']
 review=j('ac02/output/review.json');stale=j('ac02/output/stale.json')
 assert review['status']=='reviewed' and review['binding_revision']>review['previous_binding_revision']
 assert mon['held_ns']<=mon['request_ns']<=rel['monotonic_ns']<=review['started_ns']
 assert stale['status']=='refused' and stale['input_dispatched'] is False
 req,done=j('ac02/exchange/request-1.json'),j('ac02/exchange/done-1.json')
 png=raw('ac02/exchange/image-1.png');digest=hashlib.sha256(png).hexdigest()
 assert req['image_sha256']==done['image_sha256']==done['submitted_image_sha256']==digest
 assert done==r['model_response'] and done['submitted_arm']=='full' and done['ok']
 assert r['model_source']['image_sha256']==digest and r['model_source']['geometry']==[320,272,640,480]
 policy=done['grounding'];assert policy['action']=='fire' and policy['duration_ms']==1000
 px,py=policy['target_x'],policy['target_y'];gate=r['gate'];assert gate['eligible'] and gate['binding_equal'] and gate['center'] and gate['bounds']
 def observation(seq):
  matches=[n for n in z.namelist() if n.endswith('/observation-%d.json'%seq)]
  assert len(matches)==1
  return j(matches[0])
 source=observation(gate['source_sequence']);current=observation(gate['current_sequence'])
 assert source['native']['artifact']['sha256']==digest
 assert source['pointer_binding']==current['pointer_binding']
 def image_for(o):
  name=o['native']['artifact']['path'].split('/')[-1];matches=[n for n in z.namelist() if n.endswith('/images/'+name)];assert len(matches)==1
  data=raw(matches[0]);assert hashlib.sha256(data).hexdigest()==o['native']['artifact']['sha256'];return Image.open(io.BytesIO(data)).convert('RGB')
 old=image_for(source).crop((px-4,py-4,px+4,py+4)).tobytes();new=image_for(current).crop((px-4,py-4,px+4,py+4)).tobytes()
 diff=sum(abs(a-b) for a,b in zip(old,new))/len(old);colors=len(set(tuple(old[i:i+3]) for i in range(0,len(old),3)))
 assert diff==gate['difference'] and colors==gate['colors'] and diff<=32 and colors>=2
 checks=r['model_guard_checks'];assert [x['stage'] for x in checks]==['before_admission','before_focus','before_key_press:f'] and all(x['eligible'] and x['difference']<=32 for x in checks)
 action=j('ac02/output/model-action.json');assert action==r['model_action'] and action['status']=='completed' and action['admission']=='accepted'
 assert action['execution']['waits'][0]['requested_ms']==policy['duration_ms']
 releases=action['execution']['releases'];assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
 before=next(x for x in r['samples'] if x['label']=='before_model_action');after=next(x for x in r['samples'] if x['label']=='after_model_action')
 assert before['kills']==0 and after['kills']==1 and r['kill_delta']==1
 assert review['ended_ns']<=action['execution']['started_ns'] and r['keys_down_after']==[] and r['close']['release']['verified']
 assert j('ac02/exchange/closed.json')['closed'] is True
 print(json.dumps({'status':'audited','cancel_to_release_ms':(rel['monotonic_ns']-mon['request_ns'])/1e6,'policy':policy,'gate':gate,'kills':[before['kills'],after['kills']],'model_usage':done['usage'],'model_call_seconds':done['runner_ns']/1e9,'final_keys':r['keys_down_after']},indent=2))
