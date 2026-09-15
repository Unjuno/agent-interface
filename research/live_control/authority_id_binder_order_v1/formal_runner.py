from __future__ import annotations
import copy,hashlib,json,sys,tempfile
from pathlib import Path

H=Path(__file__).resolve().parent
V3DIR=H.parent/'authority_ended_validator_byte_binding_v3'
BASEDIR=H.parent/'authority_ended_restart_durability_v1'
for p in [H,V3DIR,BASEDIR]:
    if str(p) not in sys.path: sys.path.insert(0,str(p))

from authority_end_identity_binding_snapshot import bind_authority_end_identity,IdentityBindingError
from validator_byte_pinned_ledger_v3 import BytePinnedValidatorLedger

V2=V3DIR/'bridge_v2_semantic_snapshot.py'
V3=V3DIR/'validator_byte_pinned_ledger_v3.py'
BASE=BASEDIR/'durable_token_state_v2.py'
BRIDGE1=BASEDIR/'authority_ended_bridge_v1.py'
BINDER=H/'authority_end_identity_binding_snapshot.py'

EXPECTED={
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

def rejected(fn):
    try:
        fn(); return {'status':'UNEXPECTED_PASS'}
    except Exception as e:
        return {'status':'REJECTED','type':type(e).__name__,'error':str(e)}

rows=[]
def add(case,passed,detail): rows.append({'case':case,'pass':bool(passed),'detail':detail})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'
    led=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True)
    tok=led.issue(receipt(FORGED_ID))
    persisted=json.loads(p.read_text())['entries']
    add('direct_ledger_persists_forged_nonempty_id',tok.authority_end_id==FORGED_ID and persisted.get(FORGED_ID)=={'post_sequence':11,'status':'pending'}, {'token':tok.authority_end_id,'entry':persisted.get(FORGED_ID)})

with tempfile.TemporaryDirectory() as td:
    x=rejected(lambda:bind_authority_end_identity(receipt(FORGED_ID),terminal()))
    add('prebind_rejects_forged_id',x.get('type')=='IdentityBindingError' and x.get('error')=='caller authority_end_id mismatch',x)

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'
    bound=bind_authority_end_identity(receipt(),terminal())
    led=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True)
    tok=led.issue(bound)
    add('prebind_missing_id_uses_runtime_token',bound.get('authority_end_id')==RUNTIME_ID and tok.authority_end_id==RUNTIME_ID and tok.post_sequence==11, {'bound_id':bound.get('authority_end_id'),'token_id':tok.authority_end_id,'seq':tok.post_sequence})
    led2=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2)
    rt=led2.recover_pending(RUNTIME_ID)
    add('restart_recovers_prebound_runtime_token',rt.authority_end_id==RUNTIME_ID and rt.post_sequence==11, {'id':rt.authority_end_id,'seq':rt.post_sequence})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'
    led=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=True)
    led.issue(receipt(FORGED_ID))
    x=rejected(lambda:bind_authority_end_identity(receipt(FORGED_ID),terminal()))
    led2=BytePinnedValidatorLedger(p,validator_id='bridge-v2-two-capture',validator_source=V2)
    add('post_issue_binding_is_too_late',x.get('type')=='IdentityBindingError' and led2.entries.get(FORGED_ID)=={'post_sequence':11,'status':'pending'}, {'binder':x,'persisted':led2.entries.get(FORGED_ID)})

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'state.json'
    bad=terminal();bad['release']['intent_token']='different-runtime-token'
    x=rejected(lambda:bind_authority_end_identity(receipt(),bad))
    add('prebind_release_interruption_mismatch_rejects_before_state',x.get('type')=='IdentityBindingError' and x.get('error')=='release/interruption intent_token mismatch' and not p.exists(), {'binder':x,'state_exists':p.exists()})

passed=len(rows)==6 and all(r['pass'] for r in rows)
out={
    'schema':'authority-id-binder-order-v1-formal-result',
    'result_id':'authority-id-binder-order-v1-20260916-01',
    'upstream':{'identity_binder_pr':180,'identity_binder_head':'2ee3f65b4b80552619bda5e0dfc211fe276a2de5','byte_bound_ledger_pr':191,'byte_bound_ledger_head':'38048665ee020f6bd4e790807836a1a81649b0a7'},
    'rows':rows,
    'hard_gate_pass':passed,
    'decision':'RETAIN_BINDER_BEFORE_LEDGER_ORDER' if passed else 'RETAIN_FAILURE',
    'formal_retries':0,
    'dependency_sha256':{p.name:sha(p) for p in EXPECTED},
    'source_sha256':{
        'authority_end_identity_binding_snapshot.py':sha(BINDER),
        'formal_runner.py':sha(H/'formal_runner.py'),
    },
    'limitations':['offline composition semantics only','no live GUI/model/network/durable-submit','PR #168 executed-source provenance remains independent'],
}
(H/'formal-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 2)
