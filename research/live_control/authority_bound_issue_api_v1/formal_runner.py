from __future__ import annotations
import copy,hashlib,json,sys,tempfile
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent
BINDER=ROOT/'authority_end_identity_binding_v1'/'authority_end_identity_binding_v1.py'
V3=ROOT/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py'
V2=ROOT/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py'
BASE=ROOT/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py'
BRIDGE1=ROOT/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py'
CANDIDATE=H/'bound_authority_issue_v1.py'
for p in [H,ROOT/'authority_end_identity_binding_v1',ROOT/'authority_ended_validator_byte_binding_v3',ROOT/'authority_ended_restart_durability_v1']:
    if str(p) not in sys.path: sys.path.insert(0,str(p))

from bound_authority_issue_v1 import BoundAuthorityIssueLedger

EXPECTED={
    CANDIDATE:'2f812a678b72f09985e24d003b2e7030508a49e4475e9d3aef5533b1a07f2ba2',
    BINDER:'a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730',
    V3:'a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5',
    V2:'f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9',
    BASE:'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
    BRIDGE1:'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
for path,expected in EXPECTED.items():
    actual=sha(path)
    if actual!=expected: raise SystemExit(f'HASH_MISMATCH {path}: {actual} != {expected}')

RUNTIME_ID='runtime-intent-token'
FORGED_ID='caller-forged-id'
VALIDATOR_ID='bridge-v2-two-capture'

def receipt(rid=None):
    out={
        'terminal_status':'authority_ended','release_verified':True,
        'keys_down':[],'buttons_down':[],'post_release_input_admissions':0,'steps_completed':0,
        'post_authority':{
            'captures':2,'sequence':11,'sequences':[10,11],'selection_rule':'latest',
            'grants_input_authority':False,'tail_program_steps_resumed':0,
            'sequence_advanced':True,'error':None,'within_lifecycle_deadline':True,
            'snapshot_finished_ns':100,'lifecycle_deadline_ns':200,
        },
    }
    if rid is not None: out['authority_end_id']=rid
    return out

def terminal():
    return {
        'status':'authority_ended',
        'interruption':{
            'intent_token':RUNTIME_ID,
            'record':{'reason':'expired','verified':True,'keys_down':[],'buttons_down':[]},
        },
        'release':{'intent_token':RUNTIME_ID,'verified':True,'keys_down':[],'buttons_down':[]},
    }

def new_ledger(path,*,initialize=False):
    return BoundAuthorityIssueLedger(path,validator_id=VALIDATOR_ID,validator_source=V2,initialize=initialize)

def rejected(fn):
    try:
        fn(); return {'status':'UNEXPECTED_PASS'}
    except Exception as e:
        return {'status':'REJECTED','type':type(e).__name__,'error':str(e)}

rows=[]
def add(case,passed,detail): rows.append({'case':case,'pass':bool(passed),'detail':detail})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; r=receipt(); led=new_ledger(p,initialize=True); tok=led.issue(r,terminal())
    add('valid_missing_id_binds_without_mutating_caller',tok.authority_end_id==RUNTIME_ID and tok.post_sequence==11 and 'authority_end_id' not in r and led.entries=={RUNTIME_ID:{'post_sequence':11,'status':'pending'}}, {'token_id':tok.authority_end_id,'seq':tok.post_sequence,'caller_has_id':'authority_end_id' in r,'entries':led.entries})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True); before=copy.deepcopy(led.entries)
    x=rejected(lambda:led.issue(receipt(FORGED_ID),terminal()))
    add('forged_id_rejects_without_entry_mutation',x.get('type')=='IdentityBindingError' and x.get('error')=='caller authority_end_id mismatch' and led.entries==before=={}, {'rejection':x,'entries':led.entries})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True); bad=terminal();bad['release']['intent_token']='other-runtime-token';before=copy.deepcopy(led.entries)
    x=rejected(lambda:led.issue(receipt(),bad))
    add('release_token_mismatch_rejects_without_entry_mutation',x.get('type')=='IdentityBindingError' and x.get('error')=='release/interruption intent_token mismatch' and led.entries==before=={}, {'rejection':x,'entries':led.entries})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True); bad=receipt();bad['post_authority']['captures']=3;bad['post_authority']['sequences']=[10,11,12];before=copy.deepcopy(led.entries)
    x=rejected(lambda:led.issue(bad,terminal()))
    add('postbind_validator_failure_rejects_without_entry_mutation',x.get('type')=='AuthorityEndedNotReady' and led.entries==before=={}, {'rejection':x,'entries':led.entries})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True);tok=led.issue(receipt(),terminal());led2=new_ledger(p);rt=led2.recover_pending(RUNTIME_ID)
    add('restart_recovers_same_pending_runtime_token',rt.authority_end_id==RUNTIME_ID and rt.post_sequence==11 and led2.entries[RUNTIME_ID]['status']=='pending', {'id':rt.authority_end_id,'seq':rt.post_sequence,'entry':led2.entries[RUNTIME_ID]})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True);led.issue(receipt(),terminal());x=rejected(lambda:led.issue(receipt(),terminal()))
    add('duplicate_rejects_preserving_single_pending_entry',x.get('type')=='DuplicateReceipt' and led.entries=={RUNTIME_ID:{'post_sequence':11,'status':'pending'}}, {'rejection':x,'entries':led.entries})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True);tok=led.issue(receipt(),terminal());led.consume(tok);led2=new_ledger(p);x=rejected(lambda:led2.recover_pending(RUNTIME_ID))
    add('consume_restart_remains_consumed',led2.entries=={RUNTIME_ID:{'post_sequence':11,'status':'consumed'}} and x.get('type')=='TokenConsumed', {'rejection':x,'entries':led2.entries})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True);x=rejected(lambda:led.issue(receipt(),terminal(),fault='after_temp_fsync'));led2=new_ledger(p)
    add('after_temp_fsync_crash_leaves_no_issued_entry',x.get('type')=='InjectedCrash' and led2.entries=={}, {'rejection':x,'entries_after_restart':led2.entries})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'; led=new_ledger(p,initialize=True);x=rejected(lambda:led.issue(receipt(),terminal(),fault='after_replace_fsync'));led2=new_ledger(p);rt=led2.recover_pending(RUNTIME_ID)
    add('after_replace_fsync_crash_recovers_durable_runtime_id',x.get('type')=='InjectedCrash' and rt.authority_end_id==RUNTIME_ID and rt.post_sequence==11 and led2.entries=={RUNTIME_ID:{'post_sequence':11,'status':'pending'}}, {'rejection':x,'recovered_id':rt.authority_end_id,'seq':rt.post_sequence,'entries_after_restart':led2.entries})

passed=len(rows)==9 and all(r['pass'] for r in rows)
out={
    'schema':'authority-bound-issue-api-v1-formal-result',
    'result_id':'authority-bound-issue-api-v1-20260916-01',
    'base_commit':'71ab480b5a9b74e54ebae06a70913bb94ea432ef',
    'rows':rows,
    'hard_gate_pass':passed,
    'decision':'RETAIN_BOUND_ISSUE_API_V1' if passed else 'RETAIN_FAILURE',
    'formal_retries':0,
    'dependency_sha256':{p.name:sha(p) for p in EXPECTED},
    'source_sha256':{
        'bound_authority_issue_v1.py':sha(CANDIDATE),
        'formal_runner.py':sha(H/'formal_runner.py'),
    },
    'limitations':[
        'offline composition semantics only',
        'underlying Python ledger remains directly importable; this proves project-facing API order, not hostile in-process isolation',
        'identity binder bytes are not durably pinned by this wrapper across restart',
        'no live GUI/model/network/durable-submit',
        'PR #168 executed-source provenance remains independent',
    ],
}
(H/'formal-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 2)
