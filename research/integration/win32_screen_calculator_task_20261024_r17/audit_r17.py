from pathlib import Path
import hashlib,json
from PIL import Image
p=Path(__file__).resolve().parent;run=p/'run'
def j(n):return json.loads((run/n).read_text(encoding='utf-8'))
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
manifest={}
for line in (p/'FROZEN_SHA256SUMS').read_text(encoding='ascii').splitlines():h,n=line.split('  ',1);manifest[n]=h
manifest_ok=all(sha(p/n)==h for n,h in manifest.items())
conditions=json.loads((p/'conditions.json').read_text(encoding='utf-8'))
obs=j('observation-parsed.json');orr=obs['receipt']['report'];dispatch=j('dispatch-parsed.json');dr=dispatch['receipt']['report'];action=dr['supervision']['action'];custody=action['completion_custody'];verify=j('task-verification-parsed.json');vr=verify;details=j('oracle-receipts.json')[0];image=Image.open(run/'observation-image-00.png').convert('RGB');post=j('uia-post.json')['parsed'];close=j('close.json')
required={'call_id','operation_id','target_generation','oracle_id','outcome','observed_monotonic_ns','evidence_ref'}
audit={'schema':'win32-screen-calculator-r17-audit-v1','attempt_id':conditions['attempt_id'],'frozen_manifest_matches':manifest_ok,
'observation':{'status':orr['status'],'frame':orr['observation']['frame'],'region':orr['observation']['region'],'dimensions':[image.width,image.height],'image_sha256':sha(run/'observation-image-00.png'),'all_black':image.getbbox() is None,'target_generation':orr['target_generation'],'input_dispatched':orr['input_dispatched']},
'dispatch':{'wrapper_status':dispatch.get('status'),'report_status':dr['status'],'call_id':dr['call_id'],'operation_id':dr['operation_id'],'target_generation':dr['target_generation'],'input_dispatched':dr['input_dispatched'],'action_status':action['status'],'release_confirmed':action['release_confirmed'],'release_receipt':custody['completion_release_receipt'],'completion_readback':custody['completion_readback'],'replay_allowed':dr['replay_allowed']},
'effect':{'uia_before':j('uia-baseline.json')['parsed']['display_digits'],'uia_during_verifier':details['uia']['display_digits'],'uia_after':post['display_digits'],'expected':'1044'},
'task_verifier':{'status':vr['status'],'task_success':vr['task_success'],'uncertainty':vr['task_effect'].get('uncertainty'),'receipt_keys':sorted(details.keys()),'required_receipt_keys':sorted(required),'extra_keys':sorted(set(details)-required),'retry_allowed':False},
'close':{'status':close['status'],'close_release_confirmed':close['release_confirmed'],'session_state':close['session']['state'],'unresolved_call_ids':close['session']['unresolved_call_ids']},
'disposition':'HOLD_NOT_PASS: UIA read observed 1044, but server rejected the oracle receipt because the callback included extra diagnostic keys; one-use verification is immutable and was not retried.',
'scope':'One native Calculator transition only; no replay, WSLc, MAP01, blocked-I/O recovery, efficiency, or reliability claim.'}
assert manifest_ok and dr['status']=='returned' and dr['input_dispatched'] is True
assert action['release_confirmed'] is True and custody['completion_readback']['neutral'] is True
assert post['display_digits']=='1044' and vr['task_success'] is None
assert not (set(details)==required) and close['status']=='closed' and not close['session']['unresolved_call_ids']
(run/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,ensure_ascii=True,indent=2))


