"""Audit receipt-loss run and effect-reference retrieval (normal Python only)."""
from pathlib import Path
import copy,hashlib,json,zipfile
here=Path(__file__).resolve().parent;private=json.loads((here/'private-hashes.json').read_text())
with zipfile.ZipFile(here/'public.zip') as z:
 def raw(n):return z.read(n)
 def j(n):return json.loads(raw(n).decode('utf-8-sig'))
 m=j('frozen-manifest.json');assert all(hashlib.sha256(raw(k)).hexdigest()==v for k,v in m.items());c=j('ap01/conditions.json');assert hashlib.sha256(raw('frozen-manifest.json')).hexdigest()==c['manifest_sha256'] and c['launcher_sha256']==private['launch.ps1']
 assert raw('snapshot/runtime/core_v1/compiled_gui.py').replace(b'\r\n',b'\n')==(here.parents[2]/'runtime/core_v1/compiled_gui.py').read_bytes().replace(b'\r\n',b'\n')
 assert all(raw('ap01/'+n).decode('utf-8-sig').strip()=='0' for n in ('container.exit','host.exit'))
 req=j('ap01/exchange/request-1.json');resp=j('ap01/exchange/response-1.json');digest=hashlib.sha256(raw('ap01/exchange/image-1.png')).hexdigest();assert req['id']==resp['id'] and req['image_sha256']==resp['image_sha256']==digest and resp['ok'] and resp['attempted'] and resp['close_returned'] and 'ap01/exchange/request-2.json' not in z.namelist()
 original=j('ap01/output/fault-original.json');delivered=j('ap01/output/fault-delivered.json');assert original['status']=='completed' and original['execution']['releases'] and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in original['execution']['releases'])
 changed=copy.deepcopy(original);changed['execution'].pop('releases',None);changed.pop('release',None);assert changed==delivered
 r=j('ap01/output/result.json');receipt=r['method']['method_receipt'];u=receipt['unresolved_execution'];assert receipt['outcome']=='RUNTIME_FAILED' and receipt['reason']=='execution_failed' and receipt['completed_transitions']==0 and r['method']['replay_allowed'] is False and r['method']['task_success'] is None
 assert u['action']=='enter' and u['reason']=='release_unverified' and u['release_verified'] is False and u['input_dispatched'] is None
 matches=[n for n in z.namelist() if n.startswith('ap01/output/owner/') and n.endswith('/'+u['effect_ref']+'.json')];assert len(matches)==1;retained=j(matches[0]);assert retained['action_id']==u['action_id'] and retained['request']['action']=='enter' and retained['result']==delivered
 programs=[n for n in z.namelist() if n.startswith('ap01/output/owner/') and '/program-' in n and n.endswith('.json')];assert len(programs)==2 and r['fault_keyboard_calls']==1
 assert all(not (op.get('op')=='key_chord' and set(op.get('keys',[]))=={'CTRL','s'}) for n in programs for op in j(n)['ops'])
 assert hashlib.sha256(raw('ap01/output/saved.fods')).hexdigest()==hashlib.sha256(raw('blank.fods')).hexdigest()=='462beebbcb020ccf49af3cc49520f789a816cc3fb97597cefbd6940ffc26aeb1'
 assert r['saved_score']['pass_effect'] is False and not r['keys_down'] and r['buttons']==0 and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
 print(json.dumps({'status':'audited','outcome':receipt['outcome'],'reason':receipt['reason'],'unresolved_action':u['action'],'unresolved_reason':u['reason'],'effect_ref_resolved':True,'replay_allowed':False,'saved_document':'blank','actual_release_verified':True,'model_usage':resp['usage'],'model_seconds':resp['runner_ns']/1e9},indent=2))
