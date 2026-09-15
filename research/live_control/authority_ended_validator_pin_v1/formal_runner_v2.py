from __future__ import annotations
import hashlib,json,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
if (HERE/'durable_token_state_v2.py').exists(): sys.path.insert(0,str(HERE))
else: sys.path.insert(0,str(HERE.parent/'authority_ended_restart_durability_v1'))
import durable_token_state_v2 as base
if (HERE/'authority_ended_bridge_v1.py').exists():
 import authority_ended_bridge_v1 as v1
else:
 import authority_ended_bridge_v1 as v1
import bridge_v2_semantic_snapshot as v2
from validator_source_pinned_ledger_v2 import SourcePinnedValidatorLedger
V1=(HERE/'authority_ended_bridge_v1.py') if (HERE/'authority_ended_bridge_v1.py').exists() else HERE.parent/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py'
V2=HERE/'bridge_v2_semantic_snapshot.py'
def one(rid='one-epoch'):
 return {'terminal_status':'authority_ended','release_verified':True,'keys_down':[],'buttons_down':[],'post_release_input_admissions':0,'steps_completed':0,'authority_end_id':rid,'post_authority':{'captures':1,'sequence':2,'sequences':[2],'grants_input_authority':False,'tail_program_steps_resumed':0,'sequence_advanced':True,'error':None,'within_lifecycle_deadline':True,'snapshot_finished_ns':100,'lifecycle_deadline_ns':200}}
def two(rid='two-epoch',seq=11):
 return {'terminal_status':'authority_ended','release_verified':True,'keys_down':[],'buttons_down':[],'post_release_input_admissions':0,'steps_completed':0,'authority_end_id':rid,'post_authority':{'captures':2,'sequence':seq,'sequences':[seq-1,seq],'selection_rule':'latest','grants_input_authority':False,'tail_program_steps_resumed':0,'sequence_advanced':True,'error':None,'within_lifecycle_deadline':True,'snapshot_finished_ns':100,'lifecycle_deadline_ns':200}}
def rej(fn):
 try:fn();return {'status':'UNEXPECTED_PASS'}
 except Exception as e:return {'status':'REJECTED','type':type(e).__name__,'error':str(e)}
rows=[]
def add(k,ok,d):rows.append({'case':k,'pass':bool(ok),'detail':d})
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';base.to_caller_execution_decision=v2.to_caller_execution_decision;a=base.DurableTokenLedger(p,initialize=True);a.issue(two('baseline-v2'));base.to_caller_execution_decision=v1.to_caller_execution_decision;b=base.DurableTokenLedger(p);b.issue(one('baseline-v1'));o=json.loads(p.read_text());add('baseline_unpinned_drift_reproduced',set(o['entries'])=={'baseline-v1','baseline-v2'},o)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';a=SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True);t=a.issue(two());add('v2_source_pin_issues_two_capture',t.post_sequence==11 and t.authority_end_id=='two-epoch',{'id':t.authority_end_id,'seq':t.post_sequence,'sha':a.validator_sha256});o=json.loads(p.read_text());add('token_state_shape_unchanged',set(o)=={'schema','entries'} and o['schema']=='authority-ended-durable-token-state-v2',o);pin=json.loads(Path(str(p)+'.validator.json').read_text());add('sidecar_records_actual_source_hash',pin['validator_sha256']==a.validator_sha256 and pin['function_name']=='to_caller_execution_decision',pin);x=rej(lambda:a.issue(two()));add('duplicate_rejected',x.get('type')=='DuplicateReceipt',x);b=SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2);rt=b.recover_pending('two-epoch');add('matching_restart_recovers_pending',rt.post_sequence==11,{'id':rt.authority_end_id,'seq':rt.post_sequence});x=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v1-one-capture',validator_source=V1));add('validator_id_downgrade_rejected',x.get('error')=='validator pin mismatch',x);x=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V1));add('same_label_wrong_source_rejected',x.get('error')=='validator pin mismatch',x);x=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,function_name='_captures'));add('same_source_wrong_function_rejected',x.get('error')=='validator pin mismatch',x);b.consume(rt);c=SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2);x=rej(lambda:c.recover_pending('two-epoch'));add('consume_restart_remains_consumed',x.get('type')=='TokenConsumed' and c.entries['two-epoch']['status']=='consumed',{'reject':x,'entry':c.entries['two-epoch']})
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';base.to_caller_execution_decision=v1.to_caller_execution_decision;base.DurableTokenLedger(p,initialize=True);x=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v1-one-capture',validator_source=V1));add('state_without_sidecar_rejected',x.get('error')=='existing token state missing validator pin',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';base.to_caller_execution_decision=v1.to_caller_execution_decision;base.DurableTokenLedger(p,initialize=True);Path(str(p)+'.validator.json').write_text('{bad');x=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v1-one-capture',validator_source=V1));add('corrupt_sidecar_rejected',x.get('error')=='unreadable validator pin',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';a=SourcePinnedValidatorLedger(p,validator_id='bridge-v1-one-capture',validator_source=V1,initialize=True);t=a.issue(one());add('v1_source_pin_issues_one_capture',t.post_sequence==2,{'id':t.authority_end_id,'seq':t.post_sequence,'sha':a.validator_sha256});x=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2));add('v1_to_v2_reopen_rejected',x.get('error')=='validator pin mismatch',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';x=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True,fault='after_sidecar'));side=Path(str(p)+'.validator.json');y=rej(lambda:SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V1,initialize=True));z=SourcePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True);add('sidecar_only_crash_recovers_same_source_only',x.get('type')=='InjectedInitCrash' and side.exists() and y.get('error')=='validator pin mismatch' and p.exists() and z.entries=={}, {'crash':x,'mismatch':y,'state_exists':p.exists()})
passed=len(rows)==15 and all(r['pass'] for r in rows);files=['validator_source_pinned_ledger_v2.py','bridge_v2_semantic_snapshot.py','formal_runner_v2.py'];out={'schema':'authority-ended-validator-source-pin-v2-formal','result_id':'authority-ended-validator-source-pin-v2-20260916-01','base_commit':'1308b57d3209bc32b3bea5b84efb4911c915d8e9','rows':rows,'hard_gate_pass':passed,'decision':'RETAIN_SOURCE_PIN_CANDIDATE' if passed else 'RETAIN_FAILURE','formal_retries':0,'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files},'dependency_sha256':{'durable_token_state_v2.py':'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4','authority_ended_bridge_v1.py':'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e'}};Path('formal-result-v2.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if passed else 2)
