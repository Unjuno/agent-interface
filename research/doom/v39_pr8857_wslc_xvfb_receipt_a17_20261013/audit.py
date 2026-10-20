"""Independent raw-result checks for the one-shot A17 Xvfb bridge experiment."""
import hashlib, json, sys
from pathlib import Path

root=Path(__file__).resolve().parent
raw_path=root/'results/a17-01/raw.json'
raw=json.loads(raw_path.read_text(encoding='utf-8'))
errors=[]
def check(name, ok):
    if not ok: errors.append(name)
check('schema',raw.get('schema')=='pr8857-wslc-xvfb-receipt-a17-raw-v1')
check('no_candidate_error',raw.get('error') is None and raw.get('cleanup_error') is None)
check('xvfb_exit_zero',raw.get('xvfb',{}).get('exit')==0)
check('xvfb_stderr_empty',raw.get('xvfb',{}).get('stderr')=='')
code=raw.get('keycode')
events=raw.get('client_events',[])
check('positive_keycode',type(code) is int and code>0)
check('exact_press_release_pair',len(events)==2 and [e.get('type') for e in events]==[2,3])
check('event_keycode_matches',len(events)==2 and all(e.get('detail')==code for e in events))
window=raw.get('client_window')
check('target_window_matches',type(window) is int and len(events)==2 and all(e.get('window')==window for e in events))
check('server_keymap_down_then_up',raw.get('keymap')=={'while_held':True,'after_explicit_up':False})
cleanup=raw.get('owner_cleanup') or {}
terminal=(cleanup.get('records') or [{}])[-1]
check('owner_closed_and_stopped',cleanup.get('closed') is True and cleanup.get('stopped') is True and cleanup.get('thread_alive') is False)
check('terminal_empty_verified',terminal.get('event')=='owner_release' and terminal.get('verified') is True and terminal.get('keys_down')==[] and terminal.get('buttons_down')==[])
admission=raw.get('admission') or {}
check('admission_has_key_and_ordered_times',admission.get('event')=='input_admission' and admission.get('key')=='w' and type(admission.get('admitted_ns')) is int and type(admission.get('input_ack_ns')) is int and admission['admitted_ns']<=admission['input_ack_ns'])
transition=raw.get('release_transition') or {}
check('release_identity_and_bracket',transition.get('event')=='input_release_transition' and transition.get('operation')=='up' and transition.get('key')=='w' and type(transition.get('release_call_started_ns')) is int and type(transition.get('release_call_returned_ns')) is int and transition['release_call_started_ns']<=transition['release_call_returned_ns'])
check('embedded_admission_matches',transition.get('admission_receipt',{}).get('event')=='input_admission' and transition.get('admission_receipt',{}).get('key')=='w' and transition.get('admission_receipt_valid') is True)
analyzer=raw.get('analyzer') or {}
check('measurement_readiness_decision_present',type(analyzer.get('measurement_ready')) is bool)
# Hash checks bind both executable input and output to their frozen evidence paths.
hashes={}
for p in sorted((root/'INPUT').rglob('*')):
    if p.is_file(): hashes[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
raw_sha=hashlib.sha256(raw_path.read_bytes()).hexdigest()
result={'schema':'pr8857-wslc-xvfb-receipt-a17-audit-v1','checks':{k: k not in errors for k in ['schema','no_candidate_error','xvfb_exit_zero','xvfb_stderr_empty','positive_keycode','exact_press_release_pair','event_keycode_matches','target_window_matches','server_keymap_down_then_up','owner_closed_and_stopped','terminal_empty_verified','admission_has_key_and_ordered_times','release_identity_and_bracket','embedded_admission_matches','measurement_readiness_decision_present']},'errors':errors,'input_sha256':hashes,'raw_sha256':raw_sha,'observed':{'x_event_types':[e.get('type') for e in events],'keymap':raw.get('keymap'),'owner_transition_verified':transition.get('owner_transition_verified'),'ordinary_release_candidate':transition.get('ordinary_release_candidate'),'admission_owner_id_present':bool(admission.get('owner_id')),'analyzer':analyzer},'decision':'PASS_X11_RELEASE_OBSERVED_ANALYZER_BRIDGE_GAP' if not errors and analyzer.get('measurement_ready') is False else ('PASS_METHOD_SCOPED' if not errors and analyzer.get('measurement_ready') is True else 'FAIL_OR_STOP'),'scope':'One actual Xvfb/XTest key pair through PR #8857 V3 wrapper over unmodified V10 owner. No physical keyboard or application task effect.'}
(root/'results/a17-01/audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
sys.exit(0 if not errors else 1)
