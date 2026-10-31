"""Audit real GUI runs with test-only post-return release-receipt removal."""
from pathlib import Path
import copy,hashlib,json,zipfile
here=Path(__file__).resolve().parent;private=json.loads((here/'private-hashes.json').read_text());failure=json.loads((here/'setup-failure.json').read_text());assert failure['model_attempted'] is False and failure['input_programs_observed']==0 and failure['original_response_sha256']==private['prior-an01/exchange/response-1.json']
with zipfile.ZipFile(here/'public.zip') as z:
 def raw(n):return z.read(n)
 def j(n):return json.loads(raw(n).decode('utf-8-sig'))
 manifest=j('frozen-manifest.json');assert all(hashlib.sha256(raw(k)).hexdigest()==v for k,v in manifest.items());results=[]
 for arm,route in [('ao01','fresh'),('ao02','compiled')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');assert c['allocation']==arm and c['route']==r['route']==route and c['launcher_sha256']==private['launch.ps1'] and hashlib.sha256(raw('frozen-manifest.json')).hexdigest()==c['manifest_sha256']
  assert all(raw(f'{arm}/{name}').decode('utf-8-sig').strip()=='0' for name in ('container.exit','host.exit'))
  req=j(f'{arm}/exchange/request-1.json');resp=j(f'{arm}/exchange/response-1.json');digest=hashlib.sha256(raw(f'{arm}/exchange/image-1.png')).hexdigest();assert req['id']==resp['id'] and req['image_sha256']==resp['image_sha256']==digest and resp['ok'] and resp['attempted'] and resp['close_returned'] and f'{arm}/exchange/request-2.json' not in z.namelist()
  original=j(f'{arm}/output/fault-original.json');delivered=j(f'{arm}/output/fault-delivered.json');assert original['status']=='completed' and original['execution']['releases'] and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in original['execution']['releases'])
  modified=copy.deepcopy(original);modified['execution'].pop('releases',None);modified.pop('release',None);assert modified==delivered and r['fault_keyboard_calls']==1
  click=j(f'{arm}/output/click-result.json');assert click['status']=='completed' and click['execution']['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in click['execution']['releases'])
  programs=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and '/program-' in n and n.endswith('.json')];assert len(programs)==2
  ops=[j(n)['ops'] for n in programs];assert sum(any(x.get('op')=='pointer_button' for x in row) for row in ops)==1 and sum(any(x.get('op')=='text' for x in row) for row in ops)==1
  assert all(not (x.get('op')=='key_chord' and set(x.get('keys',[]))=={'CTRL','s'}) for row in ops for x in row)
  assert hashlib.sha256(raw(f'{arm}/output/saved.fods')).hexdigest()==hashlib.sha256(raw('blank.fods')).hexdigest()=='462beebbcb020ccf49af3cc49520f789a816cc3fb97597cefbd6940ffc26aeb1'
  assert r['saved_score']['pass_effect'] is False and not r['keys_down'] and r['buttons']==0 and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  if route=='fresh':
   assert r['method']=={'status':'caught_runtime_error','error':'fresh entry failed'} and f'{arm}/output/fresh-save.json' not in z.namelist() and j(f'{arm}/output/fresh-entry.json')==delivered;outcome='fresh entry failed'
  else:
   m=r['method']['method_receipt'];assert m['outcome']=='RUNTIME_FAILED' and m['reason']=='execution_failed' and m['completed_transitions']==0 and not m['transitions'] and r['method']['task_success'] is None and r['method']['replay_allowed'] is False
   terminal=[x for x in m['critical_events'] if x['event']=='action_terminal'];assert len(terminal)==1 and terminal[0]['action']=='enter' and terminal[0]['status']=='completed' and terminal[0]['release_verified'] is False
   assert f'{arm}/output/method/saved-effect.json' not in z.namelist();outcome='RUNTIME_FAILED / execution_failed'
  results.append({'arm':arm,'route':route,'outcome':outcome,'actual_release_verified':True,'delivered_release_present':False,'input_programs':len(programs),'post_fault_keyboard_calls':1,'saved_document':'blank','keys_down':[],'buttons_down':[],'model_usage':resp['usage'],'model_seconds':resp['runner_ns']/1e9})
 print(json.dumps({'status':'audited','setup_failure':failure['allocation'],'runs':results},indent=2))
