"""Audit all exact, tolerance-20 and tuned tolerance-32 attempts."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
HERE=Path(__file__).resolve().parent
outcomes={}
for group,tolerance in [('j',0),('k',20),('l',32)]:
 baseline=None
 for i in range(1,5):
  name=f'{group}{i:02}'
  with ZipFile(HERE/(name+'.zip')) as z:
   def read(path):return json.loads(z.read(path))
   c=read('conditions.json');r=read('output/result.json');assert c['allocation'].endswith(name)
   for f,h in c['inputs_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
   scripts=tuple(z.read(f) for f in ('runner.py','host.py','policy-schema.json','policy-instructions.txt'))
   if baseline is None:baseline=scripts
   else:assert baseline==scripts
   assert z.read('container.exit').decode('utf-8-sig').strip()=='0'
   if name=='k03':
    assert r['status']=='error' and 'model did not start' in r['error']
    assert read('exchange/host-error.json')['error']=='PermissionError' and r['model_calls']==0
    assert z.read('host.exit').decode('utf-8-sig').strip()=='0' # host catches and records its error
    assert r['finally_close']['release']['verified']
    print(name,'retained host file access failure before model call');continue
   assert r['status']=='completed' and r['task_success'] is None and r['model_calls']==2
   assert z.read('host.exit').decode('utf-8-sig').strip()=='0' and read('exchange/closed.json')['closed']
   gate=read('output/policy-gate.json');assert gate==r['policy_gate'];turns=[];imgs=[]
   for turn in (1,2):
    req=read(f'exchange/request-{turn}.json');done=read(f'exchange/done-{turn}.json');raw=read(f'model-call-{turn}/result.json');blob=z.read(f'exchange/image-{turn}.png')
    assert req['id']==done['id'] and done['ok'] and raw['answer_eligible'] and raw['turn_status']=='completed'
    assert hashlib.sha256(blob).hexdigest()==req['image_sha256']==done['image_sha256']
    assert raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding']
    turns.append(raw);imgs.append(Image.open(io.BytesIO(blob)).convert('RGB'))
   assert turns[0]['thread_id']==turns[1]['thread_id'] and turns[0]['call_id']!=turns[1]['call_id']
   policy=gate['policy'];assert policy==turns[0]['grounding'] and policy['action']=='fire'
   x,y=policy['target_x'],policy['target_y'];box=(x-4,y-4,x+4,y+4);patches=[im.crop(box).tobytes() for im in imgs]
   assert hashlib.sha256(patches[0]).hexdigest()==gate['old_patch_sha256'] and hashlib.sha256(patches[1]).hexdigest()==gate['current_patch_sha256']
   diff=sum(abs(a-b) for a,b in zip(*patches))/len(patches[0])
   if tolerance:assert gate['tolerance']==tolerance and abs(gate['patch_mean_abs_difference']-diff)<1e-9
   assert gate['eligible']==(gate['bounds'] and gate['center'] and gate['distinct_colors']>=2 and diff<=tolerance and gate['binding_equal'])
   samples=[json.loads(line) for line in z.read('output/samples.jsonl').splitlines()];assert samples==r['samples']
   assert any(x['label']=='turn' and 'Zombieman' in x['visible_labels'] for x in samples)
   assert all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:]))
   assert r['keys_down_after']==[] and r['close']['release_attempted'] and r['close']['release']['verified']
   for a in r['actions'][:2]:
    assert a['status']=='completed' and a['execution']['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in a['execution']['releases'])
   e=r['events'];assert e['start_1_observed_ns']<e['done_1_observed_ns']<e['start_2_observed_ns']<e['done_2_observed_ns']
   if not gate['eligible']:
    assert r['policy_disposition']=='no_action_policy_or_gate' and 'output/action-fire.json' not in z.namelist()
   else:
    fire=read('output/action-fire.json');checks=read('output/policy-guard-events.json');assert checks
    for check in checks:
     entries=[x for x in z.namelist() if x.endswith(f"/observation-{check['sequence']}.json") and '/owner/' in x];assert len(entries)==1
     obs=read(entries[0]);path=obs['native']['artifact']['path'];assert path.startswith('/out/')
     blob=z.read('output/'+path[len('/out/'):]);assert hashlib.sha256(blob).hexdigest()==obs['native']['artifact']['sha256']
     patch=Image.open(io.BytesIO(blob)).convert('RGB').crop(box).tobytes();delta=sum(abs(a-b) for a,b in zip(patch,patches[1]))/len(patch)
     assert hashlib.sha256(patch).hexdigest()==check['patch_sha256']
     if tolerance:assert abs(delta-check['mean_abs_difference'])<1e-9
     assert check['eligible']==(delta<=tolerance and check['binding_equal'] and gate['center'])
    if name in ('l02','l03'):
     mon=r['monitor'];assert mon['observed_held'] and mon['mismatch'] and mon['cancel_response']['status']=='cancel_requested'
     assert mon['cancel_response']['release_confirmed'] is False and mon['cancel_response']['review_required']
     blob=z.read('output/monitor-after.png');patch=Image.open(io.BytesIO(blob)).convert('RGB').crop(box).tobytes()
     delta=sum(abs(a-b) for a,b in zip(patch,patches[1]))/len(patch)
     assert hashlib.sha256(patch).hexdigest()==mon['observed_patch_sha256'] and abs(delta-mon['mean_abs_difference'])<1e-9 and delta>32
     ex=fire['execution'];assert fire['status']=='execution_failed' and ex['failed_op']==2 and not ex['waits'][0]['completed']
     assert 'cancellation requested' in ex['error'] and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']==2
     rel=ex['releases'];assert rel and rel[0]['verified'] and not rel[0]['keys_down'] and not rel[0]['buttons_down']
     assert ex['waits'][0]['requested_ms']==policy['duration_ms']
     assert e['start_2_observed_ns']<ex['waits'][0]['started_ns']<=mon['held_observed_ns']<e['overlay_mapped_ns']<e['cancel_requested_ns']<=e['cancel_returned_ns']<ex['waits'][0]['ended_ns']<=rel[0]['monotonic_ns']<e['policy_finished_ns']<e['done_2_observed_ns']
     print(name,'cancel to verified release ms',round((rel[0]['monotonic_ns']-e['cancel_requested_ns'])/1e6,3),'kill delta',r['kill_delta'])
    elif fire['status']=='completed':
     assert r['policy_disposition']=='completed' and fire['execution']['releases'][0]['verified']
    else:assert fire['status']=='refused' and fire['input_dispatched'] is False
   outcomes[name]=(r['status'],r.get('policy_disposition'),r.get('kill_delta'))
   print(name,'gate',gate['eligible'],'disposition',r['policy_disposition'],'kill delta',r['kill_delta'])
assert outcomes['l02'][1]=='refused_or_failed' and outcomes['l03'][1]=='refused_or_failed'
print('all 12 planned attempts retained; input effect remains unknown after cancellation')
