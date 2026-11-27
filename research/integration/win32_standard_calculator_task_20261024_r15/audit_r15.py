from pathlib import Path
import hashlib, json, re
from PIL import Image
root=Path(__file__).resolve().parents[3]
p=Path(__file__).resolve().parent
run=p/'run'
def read(name): return json.loads((run/name).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
manifest={}
for line in (p/'FROZEN_SHA256SUMS').read_text(encoding='ascii').splitlines():
 h,n=line.split('  ',1); manifest[n]=h
manifest_ok=all(sha(p/n)==h for n,h in manifest.items())
conditions=json.loads((p/'conditions.json').read_text(encoding='utf-8'))
frozen=read('FROZEN_TARGET.json')
observation=read('observation-parsed.json')
observation_report=observation['receipt']['report']
dispatch=read('dispatch-raw.txt') if False else json.loads((run/'dispatch-raw.txt').read_text(encoding='utf-8'))
dispatch_report=dispatch['receipt']['report']
action=dispatch_report['supervision']['action']
custody=action['completion_custody']
post=read('uia-post.json')['parsed']
before=read('uia-baseline.json')['parsed']
verify_exists=(run/'task-verification.json').exists()
oracle_exists=(run/'oracle-receipts.json').exists()
img=Image.open(run/'observe-image-00.png').convert('RGB')
img_extrema=img.getextrema()
all_black=(img.getbbox() is None)
close=read('close.json')
audit={
 'schema':'win32-standard-calculator-r15-audit-v1','attempt_id':conditions['attempt_id'],
 'frozen_manifest_matches':manifest_ok,'manifest_entries':len(manifest),'runner_sha256':sha(p/'run_standard_calculator.py'),
 'target_generation_observation':{'status':observation_report['status'],'input_dispatched':observation_report['input_dispatched'],'generation':observation_report['target_generation'],'generation_matches_dispatch':observation_report['target_generation']==dispatch_report['target_generation']},
 'capture':{'frame':observation_report['observation']['frame'],'region':observation_report['observation']['region'],'size':[img.width,img.height],'png_sha256':sha(run/'observe-image-00.png'),'rgb_extrema':img_extrema,'all_black':all_black,'usable_visual_observation':not all_black},
 'dispatch':{'wrapper_top_level_status':dispatch.get('status'),'nested_report_status':dispatch_report['status'],'call_id':dispatch_report['call_id'],'operation_id':dispatch_report['operation_id'],'target_generation':dispatch_report['target_generation'],'input_dispatched':dispatch_report['input_dispatched'],'action_status':action['status'],'release_confirmed':action['release_confirmed'],'release_receipt':custody['completion_release_receipt'],'completion_readback':custody['completion_readback'],'replay_allowed':dispatch_report['replay_allowed']},
 'effect':{'uia_before':before['display_digits'],'uia_after':post['display_digits'],'uia_after_expression':post['expression_name'],'expected_after':conditions['expected_display'],'exact_postcondition':post['display_digits']==conditions['expected_display']},
 'task_oracle':{'verification_file_present':verify_exists,'oracle_receipts_present':oracle_exists,'runtime_task_success':dispatch_report['task_success'],'runner_checked_top_level_status':dispatch.get('status'),'runner_would_enter_verify_branch':dispatch.get('status')=='returned','correct_nested_status_would_enter_verify_branch':dispatch_report['status']=='returned'},
 'close':{'status':close['status'],'release_confirmed_by_close_operation':close['release_confirmed'],'session_state':close['session']['state'],'unresolved_call_ids':close['session']['unresolved_call_ids'],'interpretation':'close.release_confirmed reports release performed by close itself; the completed action separately has verified release and neutral readback'},
 'strict_disposition':'HOLD_NOT_PASS: public window-client image is uniformly black and the runner skipped interface_verify_task by reading status at the wrong response nesting level; no replay is permitted',
 'scope':'One native Windows Calculator action only; no WSLc, MAP01, bounded recovery, efficiency, or reliability claim.'}
assert manifest_ok
assert audit['target_generation_observation']['generation_matches_dispatch']
assert action['status']=='completed' and action['release_confirmed'] is True
assert custody['completion_readback']['neutral'] is True
assert post['display_digits']=='1043' and all_black and not verify_exists
assert dispatch_report['status']=='returned' and dispatch.get('status') is None
(run/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
