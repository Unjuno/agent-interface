from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
with ZipFile(here/'ee01.zip') as z:
 error=json.loads(z.read('exchange/host-error.json'));assert error['error']=='AppServerUnsupportedRuntime' and error['call_id'] is None and 'ready.json' not in z.namelist()
with ZipFile(here/'ee02.zip') as z:
 read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json');e=r['events'];first=read('output/action-fire.json');review=read('output/recovery-review.json');stale=read('output/stale-after-review.json');g=r['fifth_gate'];private=read('private-local-manifest.json')
 assert z.read('host.exit').decode('utf-8-sig').strip()=='0' and z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['task_success'] is None and r['model_calls']==5
 for name,digest in c['inputs_sha256'].items():assert h(z.read(name))==digest
 assert c['route']=='inject' and c['aim_mode']=='correct' and c['fire_mode']=='withhold' and read('exchange/closed.json')['closed'] and private and all(x['size']>0 and len(x['sha256'])==64 for x in private)
 calls=[]
 for i in range(1,6):
  req=read(f'exchange/request-{i}.json');done=read(f'exchange/done-{i}.json');raw=read(f'model-call-{i}/result.json');blob=z.read(f'exchange/image-{i}.png')
  assert req['id']==done['id'] and done['ok'] and done['attempted'] and raw['answer_eligible'] and raw['turn_status']=='completed'
  assert h(blob)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'] and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low'
  assert e[f'start_{i}_observed_ns']<e[f'done_{i}_observed_ns']
  calls.append(raw)
 assert len({x['thread_id'] for x in calls})==1 and len({x['call_id'] for x in calls})==5
 assert all(e[f'done_{i}_observed_ns']<e[f'start_{i+1}_observed_ns'] for i in range(1,5))
 mon=r['monitor'];ex=first['execution'];release=ex['releases'][0];assert mon['observed_held'] and mon['mismatch'] and mon['cancel_response']['status']=='cancel_requested' and not mon['cancel_response']['release_confirmed'] and first['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed'] and release['verified'] and not release['keys_down']
 assert e['overlay_mapped_ns']<e['cancel_requested_ns']<release['monotonic_ns']<e['done_2_observed_ns']<e['overlay_removed_ns']<review['started_ns'] and review['status']=='reviewed' and not review['input_dispatched']
 assert stale['status']=='refused' and stale['input_dispatched'] is False and stale['guard_checks'][0]['status']=='MISSING'
 def obs(seq):
  names=[n for n in z.namelist() if n.endswith(f'/observation-{seq}.json') and '/owner/' in n];assert len(names)==1;return read(names[0])
 source=obs(g['source_sequence']);fresh=obs(g['checked_sequence']);blob=z.read('exchange/image-5.png');assert source['native']['artifact']['sha256']==h(blob)
 art=fresh['native']['artifact'];assert art['path'].startswith('/out/');newblob=z.read('output/'+art['path'][len('/out/'):]);assert h(newblob)==art['sha256']
 oldimg=Image.open(io.BytesIO(blob)).convert('RGB');newimg=Image.open(io.BytesIO(newblob)).convert('RGB');p=g['policy'];assert p==calls[4]['grounding'];x,y=p['target_x'],p['target_y'];box=(x-4,y-4,x+4,y+4);old=oldimg.crop(box).tobytes();now=newimg.crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(old,now))/len(old);colors=len(set(tuple(old[i:i+3]) for i in range(0,len(old),3)));geo=source['pointer_binding']['geometry'];center=abs(x-(geo[0]+geo[2]//2))<=40 and abs(y-(geo[1]+geo[3]//2))<=60
 assert g['bounds'] and g['center']==center and g['distinct_colors']==colors and abs(g['difference']-diff)<1e-9 and g['old_patch_sha256']==h(old) and g['current_patch_sha256']==h(now) and g['binding_equal']==(source['pointer_binding']==fresh['pointer_binding'])
 assert p['action']=='fire' and center and diff>32 and not g['eligible'] and r['fifth_disposition']=='no_action_policy_or_gate' and 'fifth_action' not in r
 assert r['recovery_disposition']=='no_action_policy_or_gate' and r['keys_down_after']==[] and r['close']['release_attempted'] and r['close']['release']['verified'] and r['health_delta']==-4 and r['kill_delta']==0
 sums={k:sum(x['usage'][k] for x in calls) for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')};print('fifth:',p,'patch difference',round(diff,3),'refused; usage totals',sums,'health',r['health_delta'],'kills',r['kill_delta'])
print('failed preflight and one live five-turn attempt verified')
