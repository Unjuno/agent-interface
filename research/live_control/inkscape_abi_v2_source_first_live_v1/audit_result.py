from __future__ import annotations
import hashlib,importlib.util,json
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=H.parent
RESULT=H/'formal-result.json';EVENTS=H/'events.json';RUNNER=H/'live_runner.py'
BRIDGE=ROOT/'inkscape_authority_ended_abi_v2'/'authority_ended_bridge_v2.py'
NORMALIZER=ROOT/'inkscape_authority_ended_abi_v2'/'post_authority_normalize_v2.py'
EXPECTED_RESULT='402f6320f7a87acd0540b9aab1cd2eee610fab73c9937c72a682b77f11e0e9f3'
EXPECTED_EVENTS='2504944decd52136ae773417f93d47542820a35864d0a8bc51f1f66d8017fe77'
EXPECTED_RUNNER='0cfb81a08c8387c6bddcbb3d35017fb4681d9c337a28fb62162dfd17a12243b2'
EXPECTED_BRIDGE='37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52'
EXPECTED_NORMALIZER='dc664652c7c29b002005feb7b69122d29619a449c6ad781a65ac5abfaa186d41'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
r=json.loads(RESULT.read_text());errors=[]
if sha(RESULT)!=EXPECTED_RESULT: errors.append('formal_result_hash')
if sha(EVENTS)!=EXPECTED_EVENTS: errors.append('events_hash')
if sha(RUNNER)!=EXPECTED_RUNNER: errors.append('runner_hash')
if sha(BRIDGE)!=EXPECTED_BRIDGE: errors.append('bridge_hash')
if sha(NORMALIZER)!=EXPECTED_NORMALIZER: errors.append('normalizer_hash')
if r.get('schema')!='inkscape-abi-v2-source-first-live-v1-formal-result': errors.append('schema')
if r.get('formal_seed')!=994601 or r.get('formal_retries')!=0: errors.append('formal_allocation')
if r.get('pass') is not True or r.get('decision')!='RETAIN_SOURCE_FIRST_LIVE_ABI_V2_SEMANTIC_REPRODUCTION': errors.append('formal_decision')
expected_gates={'source_identities','active_inkscape_document','shift_down_observed','expired_before_planned_hold_end','release_verified_empty','two_passive_captures_within_lifecycle','zero_post_release_input_and_tail_resume','bridge_safe_yield','svg_unchanged_no_tail_text'}
if set(r.get('gates',{}))!=expected_gates or not all(r['gates'].values()): errors.append('gates')
try:
    t=r['timing'];terminal=r['terminal'];post=terminal['post_authority_observation'];release=terminal['release']
    if not (t['expiry_detected_ns']>=t['valid_until_ns'] and t['expiry_detected_ns']<t['planned_hold_end_ns']): errors.append('expiry_timing')
    if not (t['snapshot_finished_ns']<=t['lifecycle_deadline_ns'] and t['lifecycle_slack_ns']>0): errors.append('lifecycle_timing')
    if release['verified'] is not True or release['keys_down']!=[] or release['buttons_down']!=[]: errors.append('release')
    if post['captures']!=2 or post['sequences']!=[2,3] or post['sequence']!=3 or post['selection_rule']!='latest' or post['tail_program_steps_resumed']!=0: errors.append('post_authority')
    if r['svg_sha256_before']!=r['svg_sha256_after']: errors.append('svg_changed')
except Exception as e: errors.append('detail_shape:'+type(e).__name__)
bridge=load(BRIDGE,'audit_bridge_v2')
try:
    bridge_decision=bridge.to_caller_execution_decision(r['receipt'])
except Exception as e:
    bridge_decision={'audit_error':type(e).__name__+': '+str(e)};errors.append('bridge_recompute_exception')
expected_bridge={'status':'safe_yield','reason':'authority_unavailable','completed_actions':0}
if bridge_decision!=expected_bridge: errors.append('bridge_recompute')
out={'schema':'inkscape-abi-v2-source-first-live-v1-audit','pass':not errors,'errors':errors,'formal_result_sha256':sha(RESULT),'events_sha256':sha(EVENTS),'recomputed_bridge_decision':bridge_decision,'recording_note':'formal runner overwrote the raw bridge decision field with the experiment decision string after gating; this audit independently recomputes the bridge output from the retained receipt without rerunning live input'}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
