from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json,statistics
here=Path(__file__).resolve().parent
with ZipFile(here/'pilot.zip') as z:
 read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();f=read('freeze.json');assert f['model']=='gpt-6.1-sol' and f['effort']=='low' and len(f['order'])==8
 for n,expected in f['inputs_sha256'].items():assert h(z.read('inputs/'+n))==expected
 for n,expected in f['source_adapter_sha256'].items():assert h(z.read('adapter/'+n))==expected
 for n,key in [('run.py','runner_sha256'),('policy-schema.json','schema_sha256'),('policy-instructions.txt','instructions_sha256')]:assert h(z.read(n))==f[key]
 for scene,folder,archive,index in [('positive','wslc_map01_fifth_model_recovery_20261031','ee02.zip',5),('negative','wslc_map01_bounded_model_retry_20261031','ff01.zip',6)]:
  full=Image.open(io.BytesIO(z.read('inputs/'+scene+'-full.png'))).convert('RGB');crop=Image.open(io.BytesIO(z.read('inputs/'+scene+'-crop.png'))).convert('RGB');assert full.size==(1280,1024) and crop.size==(640,480) and crop.tobytes()==full.crop(tuple(f['crop_box_full_coordinates'])).tobytes()
  with ZipFile(here.parent/folder/archive) as original:assert full.tobytes()==Image.open(io.BytesIO(original.read(f'exchange/image-{index}.png'))).convert('RGB').tobytes()
 checks=read('local-protocol-check.json');assert len(checks)==8;by_id={x['id']:x for x in checks};assert len(by_id)==8
 sessions=set();calls=set();measurements={'full':[],'crop':[]};score=0
 for c in f['order']:
  id=c['id'];r=read(id+'/summary.json');raw=read(id+'/model-call/result.json');prompt=z.read(id+'/model-call/prompt.txt').decode('utf-8');local=by_id[id]
  assert r['id']==id and r['scene']==c['scene'] and r['arm']==c['arm'] and r['status']=='completed' and r['session_closed'] and r['image_sha256']==f['inputs_sha256'][c['image']]
  assert h(prompt.encode())==f['prompt_sha256']==local['sent_prompt_sha256'] and local['sent_image_sha256']==r['image_sha256'] and local['call_id']==r['call_id'] and local['sent_turn_start_count']==1
  assert raw['call_id']==r['call_id'] and raw['grounding']==r['grounding'] and raw['usage']==r['usage'] and raw['runner_ns']==r['runner_ns'] and raw['turn_status']=='completed' and raw['answer_eligible'] and raw['requested_model']==f['model'] and raw['requested_effort']==f['effort']
  assert raw['call_id'] not in calls and raw['thread_id'] not in sessions;calls.add(raw['call_id']);sessions.add(raw['thread_id'])
  g=r['grounding'];u=r['usage'];assert 0<=u['cached_input_tokens']<=u['input_tokens'] and 0<=u['reasoning_output_tokens']<=u['output_tokens'];assert 0<=g['target_x']<c['size'][0] and 0<=g['target_y']<c['size'][1]
  if c['scene']=='positive':
   x=g['target_x']+(320 if c['arm']=='crop' else 0);y=g['target_y']+(272 if c['arm']=='crop' else 0);left,top,right,bottom=f['positive_scoring_box_full_coordinates'];correct=g['action']=='fire' and g['duration_ms']==500 and left<=x<=right and top<=y<=bottom
  else:correct=g['action']=='idle' and g['duration_ms']==0 and g['target_x']==g['target_y']==0
  score+=bool(correct);ms=r['runner_ns']/1e6;total=u['input_tokens']+u['output_tokens'];measurements[c['arm']].append((ms,total));print(id,c['scene'],c['arm'],'correct',bool(correct),'model_ms',round(ms,1),'input',u['input_tokens'],'cached',u['cached_input_tokens'],'output',u['output_tokens'])
 for arm,items in measurements.items():print(arm,'n',len(items),'median_model_ms',round(statistics.median(x[0] for x in items),1),'median_input_plus_output',statistics.median(x[1] for x in items))
 assert score==8;print('PASS:',score,'/8 coarse scene scores, unique sessions, saved image/prompt/usage linkage; local protocol attestation is not a public raw journal')
