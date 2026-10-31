"""Audit frozen inputs, two fresh decisions, guarded steering, and task counters."""
import hashlib,io,json,zipfile
from pathlib import Path
from PIL import Image
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='e5d5a6da302337fad0c7d99bd99573ff24d0b3469f99b79ced485b1ef405f0a6'
with zipfile.ZipFile(p) as z:
 def raw(n):return z.read(n)
 def j(n):return json.loads(raw(n).decode('utf-8-sig'))
 public=j('public-manifest.json');assert set(z.namelist())==set(public['files'])|{'public-manifest.json'}
 for n,h in public['files'].items():assert hashlib.sha256(raw(n)).hexdigest()==h,n
 verification=j('verification.json');assert verification['candidate_files_checked']==315 and not verification['candidate_mismatches'] and verification['wslc_list_exit']==0 and verification['running_list_empty']
 manifest=j('frozen-manifest.json');assert all(hashlib.sha256(raw(k)).hexdigest()==v for k,v in manifest.items());reports=[]
 for arm,mode in [('cc01','attack'),('cc02','wait')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');assert hashlib.sha256(raw('frozen-manifest.json')).hexdigest()==c['manifest_sha256'] and c['final_mode']==r['final_mode']==mode and c['seed']==991037 and hashlib.sha256(raw('launcher.py')).hexdigest()==c['launcher_sha256']
  launch=j(f'{arm}/launcher-result.json');assert launch['host_ready'] and launch['container_started'] and launch['container_exit']==0 and launch['host_exit']==0 and not launch['live_handle_unresolved'] and f'{arm}/exchange/host-error.json' not in z.namelist()
  assert r['status']=='completed' and r['task_success'] is None and r['keys_down_after']==[] and j(f'{arm}/exchange/closed.json')['closed']
  rel=r['close']['release'];assert rel['verified'] and not rel['keys_down'] and not rel['buttons_down']
  mon=r['cancel_monitor'];crel=r['cancel_result']['execution']['releases'][-1];review=j(f'{arm}/output/review.json');stale=j(f'{arm}/output/stale.json');assert mon['held_observed'] and mon['response']['status']=='cancel_requested' and crel['verified'] and not crel['keys_down'] and not crel['buttons_down'] and mon['held_ns']<=mon['request_ns']<=crel['monotonic_ns']<=review['started_ns'] and review['status']=='reviewed' and stale['status']=='refused' and stale['input_dispatched'] is False
  accepted=j(f'{arm}/exchange/accepted-1.json');pending=j(f'{arm}/exchange/pending-check-1.json');assert accepted==r['turn_accepted'] and pending==r['pending_check'] and pending['no_completion_observed'] and accepted['turn_id']==pending['turn_id']==r['model_responses'][0]['call_id'] and not j(f'{arm}/exchange/overlay-ready.json')['mapped']
  def obs(seq):
   matches=[n for n in z.namelist() if n.startswith(f'{arm}/output/') and n.endswith(f'/observation-{seq}.json')];assert len(matches)==1;return j(matches[0])
  def img(o):
   basename=o['native']['artifact']['path'].split('/')[-1];matches=[n for n in z.namelist() if n.startswith(f'{arm}/output/') and n.endswith('/images/'+basename)];assert len(matches)==1;data=raw(matches[0]);assert hashlib.sha256(data).hexdigest()==o['native']['artifact']['sha256'];return Image.open(io.BytesIO(data)).convert('RGB')
  def patch(im,x,y):return im.crop((x-4,y-4,x+4,y+4)).tobytes()
  def diff(a,b):assert len(a)==len(b) and a;return sum(abs(x-y) for x,y in zip(a,b))/len(a)
  assert len(r['model_responses'])==2
  for i,gname in [(1,'gate'),(2,'second_gate')]:
   done=j(f'{arm}/exchange/done-{i}.json');req=j(f'{arm}/exchange/request-{i}.json');digest=hashlib.sha256(raw(f'{arm}/exchange/image-{i}.png')).hexdigest();assert req['image_sha256']==done['image_sha256']==done['submitted_image_sha256']==digest==r[f'source{i}_digest'] and done==r['model_responses'][i-1]
   g=r[gname];a,b=obs(g['source_sequence']),obs(g['current_sequence']);policy=done['grounding'];x,y=policy['target_x'],policy['target_y'];before=patch(img(a),x,y);current=patch(img(b),x,y);assert a['native']['artifact']['sha256']==digest and a['pointer_binding']==b['pointer_binding'] and diff(before,current)==g['difference'] and g['eligible'] and g['difference']<=32 and policy['action']=='fire'
   if i==1:
    assert r['model_offset_px']==x-640 and abs(r['model_offset_px'])>5;key='d' if r['model_offset_px']>0 else 'a';assert r['steer_key']==key;action=j(f'{arm}/output/steer-action.json');assert action==r['steering'] and action['status']=='completed' and action['execution']['waits'][0]['requested_ms']==50;checks=r['steering_guard_checks'];expected=['before_admission','before_focus','before_key_press:'+key]
   elif mode=='attack':
    action=j(f'{arm}/output/final-action.json');assert action==r['final_action'] and action['status']=='completed' and action['execution']['waits'][0]['requested_ms']==200;checks=r['final_guard_checks'];expected=['before_admission','before_focus','before_key_press:f']
   else:
    assert r['final_action']=={'status':'withheld_control','input_dispatched':False} and 200_000_000<=r['wait_ended_ns']-r['wait_started_ns']<1_000_000_000;continue
   assert all(v['verified'] and not v['keys_down'] and not v['buttons_down'] for v in action['execution']['releases']) and [v['stage'] for v in checks]==expected
   for check in checks:
    o=obs(check['sequence']);assert o['pointer_binding']==b['pointer_binding'] and diff(patch(img(o),x,y),current)==check['difference'] and check['eligible'] and check['difference']<=32
   if i==2:assert r['steering']['execution']['releases'][-1]['monotonic_ns']<a['capture_ns']
  samples=r['samples'];before=next(v for v in samples if v['label']=='before_final');after=next(v for v in samples if v['label']=='after_final');coast=[v for v in samples if v['label'].startswith('final_coast_')];assert len(coast)==8
  if mode=='attack':assert r['final_action']['execution']['releases'][-1]['monotonic_ns']<=after['host_ns']
  assert after['host_ns']<coast[0]['host_ns']<coast[-1]['host_ns']
  raw_samples=[json.loads(line) for line in raw(f'{arm}/output/samples.jsonl').decode().splitlines() if line.strip()];assert raw_samples==samples
  if mode=='attack':assert [v['hits'] for v in (before,after,coast[-1])]==[0,1,1] and [v['damage'] for v in (before,after,coast[-1])]==[0,15,15]
  else:assert [v['hits'] for v in (before,after,coast[-1])]==[0,0,0] and [v['damage'] for v in (before,after,coast[-1])]==[0,0,0]
  assert all(v['hits_taken']==0 and v['damage_taken']==0 for v in (before,after,coast[-1]))
  labels=lambda name:sorted(v['name'] for v in r['scorer_labels'][name] if v['name'] in ('Zombieman','DeadZombieman','Blood'))
  reports.append({'arm':arm,'mode':mode,'policies':[v['grounding'] for v in r['model_responses']],'ammo':[before['ammo'],after['ammo'],coast[-1]['ammo']],'kills':[before['kills'],after['kills'],coast[-1]['kills']],'hits':[before['hits'],after['hits'],coast[-1]['hits']],'damage':[before['damage'],after['damage'],coast[-1]['damage']],'labels':[labels('before_final'),labels('after_final'),labels('final_coast_7')],'calls_seconds':[v['runner_ns']/1e9 for v in r['model_responses']],'usage':[v['usage'] for v in r['model_responses']]})
 assert [r['ammo'] for r in reports]==[[50,49,49],[50,50,50]] and [r['kills'] for r in reports]==[[0,0,0],[0,0,0]]
 print(json.dumps({'status':'audited','arms':reports},indent=2))
