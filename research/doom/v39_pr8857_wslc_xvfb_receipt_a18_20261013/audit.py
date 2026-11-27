"""Independent audit of the frozen A18 Xvfb raw and PR source snapshots."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
rawpath=root/'results/a18-01/raw.json'
raw=json.loads(rawpath.read_text(encoding='utf-8'))
manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
checks={}
def check(name, value): checks[name]=bool(value)
check('candidate_no_error',raw.get('error') is None and raw.get('cleanup_error') is None)
check('wslc_exit_zero',(root/'results/a18-01/container.exit').read_text().strip()=='0')
check('xvfb_exit_zero',raw.get('xvfb',{}).get('exit')==0)
code=raw.get('keycode'); events=raw.get('client_events',[])
check('same_window_keypress_keyrelease',len(events)==2 and [e.get('type') for e in events]==[2,3] and all(e.get('window')==raw.get('client_window') for e in events) and all(e.get('detail')==code for e in events))
check('independent_keymap_down_then_up',raw.get('keymap')=={'while_held':True,'after_explicit_up':False})
cleanup=raw.get('owner_cleanup') or {}; terminal=(cleanup.get('records') or [{}])[-1]
check('owner_close_verified_empty_and_stopped',cleanup.get('closed') is True and cleanup.get('stopped') is True and cleanup.get('thread_alive') is False and terminal.get('event')=='owner_release' and terminal.get('reason')=='close' and terminal.get('verified') is True and terminal.get('keys_down')==[] and terminal.get('buttons_down')==[])
admission=raw.get('admission') or {}; transition=raw.get('release_transition') or {}; embedded=transition.get('admission_receipt') or {}
check('admission_to_release_receipt_identity',admission.get('event')=='input_admission' and admission.get('key')=='w' and transition.get('operation')=='up' and transition.get('key')=='w' and embedded.get('event')=='input_admission' and embedded.get('key')=='w' and embedded.get('owner_id')==transition.get('owner_id') and embedded.get('intent_token')==transition.get('intent_token') and transition.get('admission_receipt_valid') is True)
timing=type(admission.get('input_ack_ns')) is int and type(transition.get('release_call_started_ns')) is int and type(transition.get('release_call_returned_ns')) is int and admission.get('input_ack_ns',0)<transition.get('release_call_started_ns',0)<=transition.get('release_call_returned_ns',-1)<admission.get('valid_until_ns',0)
check('monotonic_release_bracket_inside_lease',timing)
check('admission_omits_owner_id',not admission.get('owner_id'))
check('explicit_up_unverified_by_v10',transition.get('owner_transition_verified') is None and transition.get('ordinary_release_candidate') is True)
# Independently apply only the analyzer's required identity and release-verification gates.
malformed=0 if admission.get('owner_id') else 1
invalid=0 if transition.get('owner_transition_verified') is True and transition.get('ordinary_release_candidate') is True else 1
holds=1 if malformed==0 and invalid==0 else 0
ready=bool(holds and not malformed and not invalid)
observed=raw.get('analyzer') or {}
check('independent_analyzer_reconstruction',observed.get('measurement_ready') is ready and observed.get('hold_count')==holds and observed.get('malformed_admission_count')==malformed and observed.get('invalid_release_count')==invalid)
source_checks={}
repo=root.parents[2]
for entry in manifest['files']:
 p=root/entry['path']; source_checks[entry['path']+':sha256']=hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
 if entry.get('git_blob'):
  rel=entry['path'].removeprefix('INPUT/')
  blob=subprocess.check_output(['git','rev-parse',f"origin/pr/8857:{rel}"],cwd=repo,text=True).strip()
  source_checks[entry['path']+':blob']=blob==entry['git_blob']
# Confirm the exact source explains both missing fields, rather than relying only on the event.
v10=(root/'INPUT/research/live_control/input_owner_v10.py').read_text(encoding='utf-8')
wrapper=(root/'INPUT/research/live_control/input_transition_owner_v3.py').read_text(encoding='utf-8')
source_explains=("result = dict(event='input_admission', key=key, admitted_ns=admitted," in v10 and "owner_id=" not in v10[v10.find("result = dict(event='input_admission'"):v10.find("result = dict(event='input_admission'")+300] and '"owner_transition_verified": (False if explicit_keyup_failure is not None else None)' in wrapper)
source_checks['source_contract_explains_gap']=source_explains
checks['all_source_hashes_and_blobs_match']=all(source_checks.values())
checks['container_cleaned_after_rm']='No matching container listed after --rm' in (root/'results/a18-01/container-inventory-after.txt').read_text(encoding='utf-8')
all_checks=all(checks.values())
result={'schema':'pr8857-wslc-xvfb-receipt-a18-audit-v1','audit_status':'PASS' if all_checks else 'FAIL','experiment_decision':'FAIL_ANALYZER_BRIDGE' if all_checks and not ready else ('PASS_METHOD_SCOPED' if all_checks and ready else 'FAIL_OR_STOP'),'checks':checks,'source_checks':source_checks,'independent_analyzer_reconstruction':{'measurement_ready':ready,'hold_count':holds,'malformed_admission_count':malformed,'invalid_release_count':invalid},'observed':{'keycode':code,'client_events':events,'keymap':raw.get('keymap'),'top_level_admission_owner_id':admission.get('owner_id'),'release_owner_transition_verified':transition.get('owner_transition_verified'),'release_ordinary_candidate':transition.get('ordinary_release_candidate'),'admission_receipt_valid':transition.get('admission_receipt_valid'),'retained_lower_ms':(transition['release_call_started_ns']-admission['input_ack_ns'])/1e6,'retained_upper_ms':(transition['release_call_returned_ns']-admission['admitted_ns'])/1e6,'owner_terminal':terminal},'raw_sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest(),'container_log_sha256':hashlib.sha256((root/'results/a18-01/container-combined.log').read_bytes()).hexdigest(),'scope':'One synthetic XTEST key on private Xvfb. X server/client release observed; analyzer could not form a verified per-key measurement. No physical keyboard or task-effect claim.'}
(root/'results/a18-01/audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
sys.exit(0 if all_checks else 1)
