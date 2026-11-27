"""Verify stale Calc reference causes retained fail-closed yield."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
import hashlib,json
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='76f38518540286f9b72d976069ecfd45e8d5334dbe7fa493eeec21a3e31ef439'
prior=p.parent.parent/'wslc_calc_varied_pair_329_517_20261031'/'public.zip';assert hashlib.sha256(prior.read_bytes()).hexdigest()=='99ff8ee1e8940e3c88142c54638dbf94334dea132390bbc88d91fa2dd4f5a134'
with ZipFile(p) as z,ZipFile(prior) as old:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 c=j('conditions.json');v=j('verification.json');launch=j('launcher-result.json');r=j('output/result.json');prior_c=json.loads(old.read('d03/conditions.json'))
 assert c['allocation']=='d04' and c['route']=='compiled' and c['fixture']==['329','517']
 for n,h in c['input_sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 assert c['source_manifest_sha256']==prior_c['source_manifest_sha256']
 before=prior_c['input_sha256'];after=c['input_sha256'];assert set(before)==set(after) and [n for n in before if before[n]!=after[n]]==['reference.png']
 assert not v['input_mismatches'] and v['source_checked']==2092 and not v['source_mismatches'] and v['container_list_exit']==0 and not v['present']
 assert launch['container_exit']==launch['host_exit']==0 and launch['timeout'] is False
 old_img=Image.open(BytesIO(old.read('d03/reference.png'))).convert('RGB');stale=Image.open(BytesIO(z.read('reference.png'))).convert('RGB');assert old_img.size==stale.size==(1280,800)
 for box in ((100,145,123,157),(100,162,123,174)):assert old_img.crop(box).tobytes()!=stale.crop(box).tobytes()
 rec=r['method']['method_receipt'];assert rec['outcome']=='SAFE_YIELD' and rec['reason']=='effect_unavailable' and rec['completed_transitions']==1 and rec['pending_effect']['action']=='enter'
 assert [x['action'] for x in rec['transitions']]==['enter'] and rec['transitions'][0]['release_verified'] and r['method']['task_success'] is None and r['method']['replay_allowed'] is False
 trace=j('output/method/trace.json');assert trace[-1]['predicates']['cells_filled']=='unknown' and trace[-1]['predicates']['blank'] is False
 cue=j('output/method/ocr/002.json');assert cue['cue']=='unknown' and cue['source_context_verified'] and cue['input_dispatched'] is False
 assert j('output/method/guard-events.json')==[] and 'output/method/saved-effect.json' not in z.namelist()
 executions=[n for n in z.namelist() if n.startswith('output/owner/') and n.endswith('-execution.json')];assert len(executions)==1
 execution=j(executions[0]);assert execution['request']['action']=='enter' and execution['result']['status']=='completed'
 releases=execution['result']['execution']['releases'];assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
 click=j('output/click-result.json');releases=click['execution']['releases'];assert click['status']=='completed' and releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
 assert z.read('output/saved.fods')==z.read('blank.fods') and r['saved_score']['pass_effect'] is False
 assert not r['keys_down'] and r['buttons']==0 and r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
 req=j('exchange/request-1.json');resp=j('exchange/response-1.json');raw=j('model-call-1/result.json');assert req['id']==resp['id'] and resp['ok'] and resp['attempted'] and resp['close_returned'] and hashlib.sha256(z.read('exchange/image-1.png')).hexdigest()==req['image_sha256']==resp['image_sha256']
 assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['turn_status']=='completed'
 assert 'exchange/request-2.json' not in z.namelist() and raw['call_id']!=json.loads(old.read('d03/exchange/response-1.json'))['call_id']
 u=raw['usage'];assert 0<=u['cached_input_tokens']<=u['input_tokens']
 print(json.dumps({'status':'audited','negative_control':'pass','task':'not completed','outcome':rec['outcome'],'reason':rec['reason'],'executed_actions':['enter'],'saved_file':'byte-identical blank','model_calls':1,'input_tokens':u['input_tokens'],'cached_input_subset':u['cached_input_tokens'],'output_tokens':u['output_tokens']},indent=2))
