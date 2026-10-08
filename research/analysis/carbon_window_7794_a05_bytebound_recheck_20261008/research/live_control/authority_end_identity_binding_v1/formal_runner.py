from __future__ import annotations
import copy, hashlib, importlib, json, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
if (HERE/'durable_token_state_v2.py').exists():
    sys.path.insert(0,str(HERE))
else:
    sys.path.insert(0,str(HERE.parent/'authority_ended_restart_durability_v1'))
import durable_token_state_v2 as tokenmod
from authority_end_identity_binding_v1 import bind_authority_end_identity
import bridge_v2_semantic_snapshot as bridge2

tokenmod.to_caller_execution_decision=bridge2.to_caller_execution_decision
fixture=json.loads((HERE/'retained_terminal_fixture.json').read_text())
term0=fixture['terminal']; stopped=fixture['input_stopped_ns']
admissions=sum(1 for e in fixture['input_events'] if e.get('admitted_ns',0)>stopped)
def receipt():
    r=term0['release']
    return {'terminal_status':term0['status'],'release_verified':r['verified'],'keys_down':copy.deepcopy(r['keys_down']),
            'buttons_down':copy.deepcopy(r['buttons_down']),'post_release_input_admissions':admissions,
            'steps_completed':term0['steps_completed'],'post_authority':copy.deepcopy(term0['post_authority_observation'])}
def reject(fn):
    try: fn(); return {'status':'UNEXPECTED_PASS'}
    except Exception as e:return {'status':'REJECTED','type':type(e).__name__,'error':str(e)}
rows=[]
def add(case,ok,detail):rows.append({'case':case,'pass':bool(ok),'detail':detail})
r=receipt();t=copy.deepcopy(term0);rid=t['interruption']['intent_token'];b=bind_authority_end_identity(r,t)
add('valid_two_capture_binds_existing_intent_token',b['authority_end_id']==rid and bridge2.to_caller_execution_decision(b)=={'status':'safe_yield','reason':'authority_unavailable','completed_actions':0},{'id':rid,'seq':b['post_authority']['sequence']})
add('identity_exists_before_post_authority_capture',fixture['input_stopped_emit_ns']<fixture['first_post_authority_capture_ns'] and fixture['terminal']['interruption']['intent_token']==rid,{'stop_emit_ns':fixture['input_stopped_emit_ns'],'first_capture_ns':fixture['first_post_authority_capture_ns'],'id':rid})
with tempfile.TemporaryDirectory(prefix='authority-end-id-formal-') as td:
    p=Path(td)/'token.json'; led=tokenmod.DurableTokenLedger(p,initialize=True);tok=led.issue(copy.deepcopy(b))
    add('durable_issue_preserves_exact_runtime_id',tok.authority_end_id==rid and tok.post_sequence==11 and led.entries[rid]=={'post_sequence':11,'status':'pending'},{'id':tok.authority_end_id,'seq':tok.post_sequence,'entry':led.entries[rid]})
    x=reject(lambda:led.issue(copy.deepcopy(b)));add('duplicate_same_receipt_rejected',x.get('type')=='DuplicateReceipt' and x.get('error')=='authority_end_id already exists',x)
    alt=copy.deepcopy(b);alt['post_authority']['sequences']=[10,12];alt['post_authority']['sequence']=12
    x=reject(lambda:led.issue(alt));add('same_epoch_altered_post_sequence_rejected',x.get('type')=='DuplicateReceipt' and x.get('error')=='authority_end_id already exists',x)
    led2=tokenmod.DurableTokenLedger(p);rt=led2.recover_pending(rid);add('restart_recovers_pending_same_id',rt.authority_end_id==rid and rt.post_sequence==11,{'id':rt.authority_end_id,'seq':rt.post_sequence})
    t2=copy.deepcopy(t);t2['interruption']['intent_token']='distinct-runtime-intent-token';t2['release']['intent_token']='distinct-runtime-intent-token'
    r2=receipt();r2['post_authority']['sequences']=[12,13];r2['post_authority']['sequence']=13;b2=bind_authority_end_identity(r2,t2);u=led2.issue(b2)
    add('distinct_runtime_intent_token_issues_separately',u.authority_end_id=='distinct-runtime-intent-token' and u.post_sequence==13,{'id':u.authority_end_id,'seq':u.post_sequence})
missing=copy.deepcopy(t);missing['interruption'].pop('intent_token');x=reject(lambda:bind_authority_end_identity(r,missing));add('missing_intent_token_rejected',x.get('error')=='runtime interruption intent_token required',x)
forged=receipt();forged['authority_end_id']='caller-forged-id';x=reject(lambda:bind_authority_end_identity(forged,t));add('mismatched_caller_id_rejected',x.get('error')=='caller authority_end_id mismatch',x)
legacy=copy.deepcopy(t);legacy['status']='expired';x=reject(lambda:bind_authority_end_identity(r,legacy));add('legacy_expired_not_promoted',x.get('error')=='authority_ended terminal required',x)
unverified=copy.deepcopy(t);unverified['interruption']['record']['verified']=False;x=reject(lambda:bind_authority_end_identity(r,unverified));add('unverified_interruption_rejected',x.get('error')=='verified empty expiry interruption required',x)
focus=copy.deepcopy(t);focus['interruption']['record']['reason']='focus_changed';x=reject(lambda:bind_authority_end_identity(r,focus));add('non_expiry_interruption_rejected',x.get('error')=='verified expiry interruption required',x)
mismatch=copy.deepcopy(t);mismatch['release']['intent_token']='different-release-token';x=reject(lambda:bind_authority_end_identity(r,mismatch));add('release_token_mismatch_rejected',x.get('error')=='release/interruption intent_token mismatch',x)
passed=len(rows)==13 and all(q['pass'] for q in rows)
files=['authority_end_identity_binding_v1.py','bridge_v2_semantic_snapshot.py','retained_terminal_fixture.json','formal_runner.py']
result={'schema':'authority-end-identity-binding-v1-formal-result','result_id':'authority-end-identity-binding-v1-20260916-01','base_commit':'1308b57d3209bc32b3bea5b84efb4911c915d8e9','rows':rows,'hard_gate_pass':passed,'decision':'RETAIN_INTENT_TOKEN_BINDING' if passed else 'RETAIN_FAILURE','runtime_identity':rid,'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files},'dependency_sha256':{'authority_ended_restart_durability_v1/durable_token_state_v2.py':hashlib.sha256((HERE/'durable_token_state_v2.py').read_bytes()).hexdigest() if (HERE/'durable_token_state_v2.py').exists() else '72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4'},'formal_retries':0,'limitations':['offline interface semantics','retained PR #168 terminal projection used as data only','PR #168 formal source provenance remains separate','bridge-v2 semantic snapshot is not a certification of PR #168 executed bytes','no GUI/model/network/durable-submit transport']}
(HERE/'formal-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if passed else 2)
