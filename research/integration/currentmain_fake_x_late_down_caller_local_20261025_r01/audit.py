import hashlib
import json
from pathlib import Path
import sys
root=Path(__file__).parent
raw=root/'raw'
manifest=json.loads((root/'RAW-SHA256.json').read_text(encoding='utf-8'))
by_name={x['name']:x for x in manifest['files']}
checks=[]
def check(name, condition): checks.append({'name':name,'passed':bool(condition)})
check('test_exit_zero',(root/'exit-code.txt').read_text().strip()=='0')
log=(root/'test.log').read_text(encoding='utf-8')
check('one_unittest_ok','Ran 1 test' in log and log.rstrip().endswith('OK'))
check('all_raw_files_manifested',len(by_name)==len(list(raw.iterdir())) and len(by_name)==8)
check('raw_hashes_and_sizes_match',all((raw/x['name']).is_file() and (raw/x['name']).stat().st_size==x['bytes'] and hashlib.sha256((raw/x['name']).read_bytes()).hexdigest()==x['sha256'] for x in manifest['files']))
required={'standard-caller-result.json','fake-x-release-readback.json','fake-x-late-down.json','fake-x-server-queue.json','held-reply.json','synthetic-effect-receipt.json'}
check('required_raw_receipts_present',required.issubset(by_name))
result=json.loads((raw/'standard-caller-result.json').read_text())
release=result['synthetic_late_down']['release_readback']; late=result['synthetic_late_down']['late_down']; queue=result['synthetic_late_down']['queue']
check('modeled_release_before_modeled_late_down',release['event_index']<late['event_index'] and late['modeled_after_release_readback'] is True and late['protocol_order_is_modeled_not_observed'] is True)
check('synthetic_key_is_down_after_late_delivery',release['keys_down']==[] and late['keys_down_after_delivery']==[2] and queue['state']=='accepted_and_held_in_synthetic_queue')
check('release_receipt_is_not_promoted_to_public_success',result['cancel']['owner_release_attempt']['status']=='readback_verified' and result['cancel']['release_confirmed'] is False and result['cancel']['cleanup_status']=='UNKNOWN')
check('terminal_unknown_no_replay_and_no_task_success',result['terminal']['status']=='runtime_failed' and result['terminal']['cleanup_status']=='UNKNOWN' and result['terminal']['release_confirmed'] is False and result['terminal']['task_success'] is None and result['terminal']['replay_allowed'] is False)
check('old_request_risk_retained',result['cancel']['late_server_request_possible'] is True)
check('fake_effect_not_task_success',json.loads((raw/'synthetic-effect-receipt.json').read_text())['task_success'] is None)
source=json.loads((root/'PREREGISTRATION.json').read_text())['source_files']
check('all_test_source_hashes_equal_origin_main',all(v['equal'] and v['working_sha256']==v['origin_main_sha256'] for v in source.values()))
aud={'status':'PASS_SCOPED' if all(x['passed'] for x in checks) else 'FAIL','checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks,'scope':'local Python Fake X contract only; synthetic queue ordering; no WSLc, real X, OS input, task success or reliability claim'}
(root/'AUDIT.json').write_text(json.dumps(aud,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(aud,indent=2))
sys.exit(0 if aud['status']=='PASS_SCOPED' else 1)
