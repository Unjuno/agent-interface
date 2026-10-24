from pathlib import Path
import hashlib,json,re
from PIL import Image
p=Path(__file__).resolve().parent;run=p/'run'
def j(n):return json.loads((run/n).read_text(encoding='utf-8'))
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
conditions=json.loads((p/'conditions.json').read_text(encoding='utf-8'))
manifest={}
for line in (p/'FROZEN_SHA256SUMS').read_text(encoding='ascii').splitlines():h,n=line.split('  ',1);manifest[n]=h
manifest_ok=all(sha(p/n)==h for n,h in manifest.items())
obs=j('observation-parsed.json');orpt=obs['receipt']['report'];dwrap=j('dispatch-parsed.json');dr=dwrap['receipt']['report'];action=dr['supervision']['action'];custody=action['completion_custody'];verify=j('task-verification-parsed.json');final=j('final-results-parsed.json');receipts=j('oracle-receipts.json');details=j('oracle-details.json');pre=j('uia-baseline.json')['parsed'];post=j('uia-post.json')['parsed'];close=j('close.json');img=Image.open(run/'observation-image-00.png').convert('RGB')
required={'call_id','operation_id','target_generation','oracle_id','outcome','observed_monotonic_ns','evidence_ref'}
receipt=receipts[0]
same=receipt['call_id']==dr['call_id']==verify['call_id']==final['call_id'] and receipt['operation_id']==dr['operation_id']==action['operation_id'] and receipt['target_generation']==dr['target_generation']==orpt['target_generation']
result={'schema':'win32-screen-calculator-r19-audit-v1','attempt_id':conditions['attempt_id'],'frozen_manifest_matches':manifest_ok,'visual_observation':{'status':orpt['status'],'frame':orpt['observation']['frame'],'region':orpt['observation']['region'],'dimensions':[img.width,img.height],'png_sha256':sha(run/'observation-image-00.png'),'all_black':img.getbbox() is None,'visually_inspected':'Calculator showed 1,044 before dispatch'},'dispatch':{'call_id':dr['call_id'],'operation_id':dr['operation_id'],'target_generation':dr['target_generation'],'status':dr['status'],'input_dispatched':dr['input_dispatched'],'action_status':action['status'],'release_confirmed':action['release_confirmed'],'release_receipt':custody['completion_release_receipt'],'completion_readback':custody['completion_readback'],'replay_allowed':dr['replay_allowed']},'task_effect':{'receipt_exact_schema':set(receipt)==required,'receipt_keys':sorted(receipt),'outcome':receipt['outcome'],'same_call_operation_generation':same,'verifier_status':verify['status'],'verifier_task_success':verify['task_success'],'retained_task_success':final['task_success'],'uia_before':pre['display_digits'],'uia_at_oracle':details[0]['uia']['display_digits'],'uia_after':post['display_digits'],'expected':'1045'},'close':{'status':close['status'],'close_release_confirmed':close['release_confirmed'],'session_state':close['session']['state'],'unresolved_call_ids':close['session']['unresolved_call_ids']},'strict_disposition':'PASS_SCOPED: one visibly grounded physical-screen Calculator action achieved exact UIA task effect, exact-schema task_success certificate, verified release, neutral readback, and close without unresolved calls.','limits':'One native Windows Calculator sample; no WSLc, MAP01, blocked-I/O recovery, matched efficiency, or reliability conclusion.'}
assert manifest_ok and orpt['status']=='returned' and orpt['input_dispatched'] is False and img.size==(320,533) and img.getbbox() is not None
assert dr['status']=='returned' and dr['input_dispatched'] is True and action['status']=='completed' and action['release_confirmed'] is True
assert custody['completion_readback']['neutral'] is True and custody['completion_readback']['operation_id']==dr['operation_id'] and custody['completion_readback']['target_generation']==dr['target_generation']
assert set(receipt)==required and receipt['outcome']=='success' and same
assert verify['status']=='verified' and verify['task_success'] is True and final['task_success'] is True
assert pre['display_digits']=='1044' and details[0]['uia']['display_digits']=='1045' and post['display_digits']=='1045'
assert close['status']=='closed' and not close['session']['unresolved_call_ids'] and dr['replay_allowed'] is False
(run/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
