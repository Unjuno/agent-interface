from __future__ import annotations
import hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
for p in [H, H.parent/'authority_ended_restart_durability_v1', H.parent/'authority_ended_validator_pin_v1']:
    if p.exists() and str(p) not in sys.path: sys.path.insert(0,str(p))
import durable_token_state_v2 as base
import authority_ended_bridge_v1 as bridge1
import bridge_v2_semantic_snapshot as bridge2
from validator_source_pinned_ledger_v2 import SourcePinnedValidatorLedger
from validator_byte_pinned_ledger_v3 import BytePinnedValidatorLedger
V1=Path(bridge1.__file__)
V2=Path(bridge2.__file__)
A=b"def to_caller_execution_decision(receipt):\n    raise ValueError('A rejects')\n"
B=b"def to_caller_execution_decision(receipt):\n    return {'status':'safe_yield','reason':'authority_unavailable','completed_actions':receipt['steps_completed']}\n"
def one(rid='one-epoch'):
 return {'terminal_status':'authority_ended','release_verified':True,'keys_down':[],'buttons_down':[],'post_release_input_admissions':0,'steps_completed':0,'authority_end_id':rid,'post_authority':{'captures':1,'sequence':2,'sequences':[2],'grants_input_authority':False,'tail_program_steps_resumed':0,'sequence_advanced':True,'error':None,'within_lifecycle_deadline':True,'snapshot_finished_ns':100,'lifecycle_deadline_ns':200}}
def two(rid='two-epoch',seq=11):
 return {'terminal_status':'authority_ended','release_verified':True,'keys_down':[],'buttons_down':[],'post_release_input_admissions':0,'steps_completed':0,'authority_end_id':rid,'post_authority':{'captures':2,'sequence':seq,'sequences':[seq-1,seq],'selection_rule':'latest','grants_input_authority':False,'tail_program_steps_resumed':0,'sequence_advanced':True,'error':None,'within_lifecycle_deadline':True,'snapshot_finished_ns':100,'lifecycle_deadline_ns':200}}
def reject(fn):
 try: fn(); return {'status':'UNEXPECTED_PASS'}
 except Exception as e: return {'status':'REJECTED','type':type(e).__name__,'error':str(e)}
rows=[]
def add(case,ok,detail): rows.append({'case':case,'pass':bool(ok),'detail':detail})
def replacement_case(cls,td,name):
 p=Path(td)/'validator.py';p.write_bytes(A);state=Path(td)/(name+'.json');orig=Path.read_bytes;done=False
 def hooked(self):
  nonlocal done
  data=orig(self)
  if self==p and not done:
   done=True;p.write_bytes(B)
  return data
 with patch.object(Path,'read_bytes',hooked):
  led=cls(state,validator_id='race',validator_source=p,initialize=True)
  pin=json.loads(Path(str(state)+'.validator.json').read_text())
  outcome=reject(lambda:led.issue(one(name)))
  if outcome['status']=='UNEXPECTED_PASS': outcome={'status':'ISSUED'}
 return {'outcome':outcome,'pin_sha':pin['validator_sha256'],'A_sha':hashlib.sha256(A).hexdigest(),'B_sha':hashlib.sha256(B).hexdigest(),'final_file_sha':hashlib.sha256(p.read_bytes()).hexdigest()}
with tempfile.TemporaryDirectory() as td:
 r=replacement_case(SourcePinnedValidatorLedger,td,'v2-race');add('v2_hash_to_load_toctou_reproduced',r['outcome']=={'status':'ISSUED'} and r['pin_sha']==r['A_sha'] and r['final_file_sha']==r['B_sha'],r)
with tempfile.TemporaryDirectory() as td:
 r=replacement_case(BytePinnedValidatorLedger,td,'v3-race');add('v3_executes_exact_hashed_bytes_under_same_replacement',r['outcome'].get('type')=='ValueError' and r['outcome'].get('error')=='A rejects' and r['pin_sha']==r['A_sha'] and r['final_file_sha']==r['B_sha'],r)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'state.json';led=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True);tok=led.issue(two());add('v3_v2_source_issues_two_capture',tok.authority_end_id=='two-epoch' and tok.post_sequence==11,{'id':tok.authority_end_id,'seq':tok.post_sequence,'sha':led.validator_sha256});state=json.loads(p.read_text());add('token_state_shape_unchanged',set(state)=={'schema','entries'} and state['schema']=='authority-ended-durable-token-state-v2',state);pin=json.loads(Path(str(p)+'.validator.json').read_text());add('v3_sidecar_binds_actual_hash_and_function',pin['validator_sha256']==hashlib.sha256(V2.read_bytes()).hexdigest() and pin['function_name']=='to_caller_execution_decision',pin);led2=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2);rt=led2.recover_pending('two-epoch');add('v3_matching_restart_recovers_pending',rt.post_sequence==11,{'id':rt.authority_end_id,'seq':rt.post_sequence});x=reject(lambda:led2.issue(two()));add('v3_duplicate_rejected',x.get('type')=='DuplicateReceipt' and x.get('error')=='authority_end_id already exists',x);led2.consume(rt);led3=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2);x=reject(lambda:led3.recover_pending('two-epoch'));add('v3_consume_restart_remains_consumed',x.get('type')=='TokenConsumed' and led3.entries['two-epoch']['status']=='consumed',{'reject':x,'entry':led3.entries['two-epoch']});tmp=V2.read_bytes();mut=Path(td)/'changed.py';mut.write_bytes(tmp+b'\n# changed\n');x=reject(lambda:BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=mut));add('v3_changed_source_reopen_rejected',x.get('error')=='validator pin mismatch',x);x=reject(lambda:BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,function_name='_captures'));add('v3_wrong_function_rejected',x.get('error')=='validator pin mismatch',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'bad.py';p.write_text('def x(:\n');x=reject(lambda:BytePinnedValidatorLedger(Path(td)/'s.json',validator_id='syntax',validator_source=p,initialize=True));add('v3_syntax_error_rejected',x.get('error')=='validator source execution failed',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'missing.py';p.write_text('x=1\n');x=reject(lambda:BytePinnedValidatorLedger(Path(td)/'s.json',validator_id='missing',validator_source=p,initialize=True));add('v3_missing_function_rejected',x.get('error')=='validator callable missing',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';base.to_caller_execution_decision=bridge1.to_caller_execution_decision;base.DurableTokenLedger(p,initialize=True);x=reject(lambda:BytePinnedValidatorLedger(p,validator_id='bridge-v1-one-capture',validator_source=V1));add('v3_state_without_sidecar_rejected',x.get('error')=='existing token state missing validator pin',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';base.to_caller_execution_decision=bridge1.to_caller_execution_decision;base.DurableTokenLedger(p,initialize=True);Path(str(p)+'.validator.json').write_text('{bad');x=reject(lambda:BytePinnedValidatorLedger(p,validator_id='bridge-v1-one-capture',validator_source=V1));add('v3_corrupt_sidecar_rejected',x.get('error')=='unreadable validator pin',x)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';x=reject(lambda:BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True,fault='after_sidecar'));y=reject(lambda:BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V1,initialize=True));z=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True);add('v3_sidecar_only_crash_same_bytes_only',x.get('type')=='InjectedInitCrash' and y.get('error')=='validator pin mismatch' and z.entries=={}, {'crash':x,'mismatch':y,'state_exists':p.exists()})
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'s.json';led=BytePinnedValidatorLedger(p,validator_id='bridge-v1-one-capture',validator_source=V1,initialize=True);t=led.issue(one());add('v3_v1_source_issues_one_capture',t.post_sequence==2,{'id':t.authority_end_id,'seq':t.post_sequence,'sha':led.validator_sha256});x=reject(lambda:BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2));add('v3_v1_to_v2_reopen_rejected',x.get('error')=='validator pin mismatch',x)
passed=len(rows)==17 and all(r['pass'] for r in rows)
files=['validator_byte_pinned_ledger_v3.py','bridge_v2_semantic_snapshot.py','formal_runner_v3_02.py']
out={'schema':'authority-ended-validator-byte-binding-v3-formal','result_id':'authority-ended-validator-byte-binding-v3-20260916-02','base_research_head':'6eca918728e43c4bbf787ccdf8ccd848c681c537','rows':rows,'hard_gate_pass':passed,'decision':'RETAIN_BYTE_BOUND_VALIDATOR_V3' if passed else 'RETAIN_FAILURE','formal_retries':0,'source_sha256':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in files},'dependency_sha256':{'validator_source_pinned_ledger_v2.py':'189bd81dd884b7840b31ef01e453e62a6d850f5c14dbe925bce8fb4b016558d2','durable_token_state_v2.py':'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4','authority_ended_bridge_v1.py':'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e'}}
(H/'formal-result-v3.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if passed else 2)
