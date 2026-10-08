from __future__ import annotations
import json,os,shutil,sys
from pathlib import Path

sim=Path(os.environ['SIM_ROOT']).resolve()
candidate_dir=sim/'research'/'live_control'/'authority_binder_byte_pin_v1'
if str(candidate_dir) not in sys.path:
    sys.path.insert(0,str(candidate_dir))
from binder_byte_pinned_bound_issue_v1 import BinderBytePinnedBoundIssueLedger

RUNTIME_ID='runtime-intent-token'
FORGED_ID='caller-forged-id'
BINDER_ID='authority-end-intent-token-v1'
VALIDATOR_ID='bridge-v2-two-capture'
ACTIVE_BINDER=sim/'active_binder.py'
VALIDATOR=sim/'research'/'live_control'/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py'

def receipt(caller):
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
    if caller=='forged':
        out['authority_end_id']=FORGED_ID
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

def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None

def disk_snapshot(state):
    state=Path(state)
    return {
        'state_exists':state.exists(),
        'entries_on_disk':(read_json(state) or {}).get('entries') if state.exists() else None,
        'binder_pin_exists':Path(str(state)+'.binder.json').exists(),
        'binder_pin':read_json(Path(str(state)+'.binder.json')),
        'validator_pin_exists':Path(str(state)+'.validator.json').exists(),
        'validator_pin':read_json(Path(str(state)+'.validator.json')),
    }

def make(state,initialize,constructor_fault):
    return BinderBytePinnedBoundIssueLedger(
        state,
        binder_id=BINDER_ID,
        binder_source=ACTIVE_BINDER,
        validator_id=VALIDATOR_ID,
        validator_source=VALIDATOR,
        initialize=initialize,
        fault=None if constructor_fault=='none' else constructor_fault,
    )

def rejected(e,state,ledger=None):
    out={'status':'REJECTED','type':type(e).__name__,'error':str(e),**disk_snapshot(state)}
    if ledger is not None:
        out['binder_sha256']=ledger.binder_sha256
        out['validator_sha256']=ledger.validator_sha256
        out['entries_in_memory']=ledger.entries
    return out

mode=sys.argv[1]
state=Path(sys.argv[2])
initialize=sys.argv[3]=='1'
constructor_fault=sys.argv[4]
try:
    ledger=make(state,initialize,constructor_fault)
    if mode=='init_only':
        out={'status':'INITIALIZED','binder_sha256':ledger.binder_sha256,'validator_sha256':ledger.validator_sha256,'entries_in_memory':ledger.entries,**disk_snapshot(state)}
    elif mode=='issue':
        caller=sys.argv[5];issue_fault=sys.argv[6]
        tok=ledger.issue(receipt(caller),terminal(),fault=None if issue_fault=='none' else issue_fault)
        out={'status':'ISSUED','token_id':tok.authority_end_id,'seq':tok.post_sequence,'binder_sha256':ledger.binder_sha256,'validator_sha256':ledger.validator_sha256,'entries_in_memory':ledger.entries,**disk_snapshot(state)}
    elif mode=='recover':
        rid=sys.argv[5]
        tok=ledger.recover_pending(rid)
        out={'status':'RECOVERED','token_id':tok.authority_end_id,'seq':tok.post_sequence,'binder_sha256':ledger.binder_sha256,'validator_sha256':ledger.validator_sha256,'entries_in_memory':ledger.entries,**disk_snapshot(state)}
    elif mode=='loaded_drift_issue':
        drift=Path(sys.argv[5]);caller=sys.argv[6]
        shutil.copyfile(drift,ACTIVE_BINDER)
        try:
            tok=ledger.issue(receipt(caller),terminal())
            out={'status':'ISSUED','token_id':tok.authority_end_id,'seq':tok.post_sequence,'binder_sha256':ledger.binder_sha256,'validator_sha256':ledger.validator_sha256,'entries_in_memory':ledger.entries,**disk_snapshot(state)}
        except Exception as e:
            out=rejected(e,state,ledger)
    else:
        raise ValueError('unknown mode')
except Exception as e:
    out=rejected(e,state,locals().get('ledger'))
print(json.dumps(out,sort_keys=True))
