from __future__ import annotations
import json,os,sys
from pathlib import Path

sim=Path(os.environ['SIM_ROOT']).resolve()
candidate_dir=sim/'research'/'live_control'/'authority_binder_byte_pin_v1'
if str(candidate_dir) not in sys.path:
    sys.path.insert(0,str(candidate_dir))
from binder_byte_pinned_bound_issue_v1 import BinderBytePinnedBoundIssueLedger

RUNTIME_ID='runtime-intent-token'
BINDER_ID='authority-end-intent-token-v1'
VALIDATOR_ID='bridge-v2-two-capture'
ACTIVE_BINDER=sim/'active_binder.py'
ACTIVE_VALIDATOR=sim/'active_validator.py'

def receipt():
    return {
        'terminal_status':'authority_ended','release_verified':True,
        'keys_down':[],'buttons_down':[],'post_release_input_admissions':0,'steps_completed':0,
        'post_authority':{
            'captures':2,'sequence':11,'sequences':[10,11],'selection_rule':'latest',
            'grants_input_authority':False,'tail_program_steps_resumed':0,
            'sequence_advanced':True,'error':None,'within_lifecycle_deadline':True,
            'snapshot_finished_ns':100,'lifecycle_deadline_ns':200,
        },
    }

def terminal():
    return {
        'status':'authority_ended',
        'interruption':{'intent_token':RUNTIME_ID,'record':{'reason':'expired','verified':True,'keys_down':[],'buttons_down':[]}},
        'release':{'intent_token':RUNTIME_ID,'verified':True,'keys_down':[],'buttons_down':[]},
    }

def read_json(path):
    try: return json.loads(Path(path).read_text())
    except Exception: return None

def snapshot(state):
    state=Path(state)
    return {
        'state_exists':state.exists(),
        'entries_on_disk':(read_json(state) or {}).get('entries') if state.exists() else None,
        'binder_pin_exists':Path(str(state)+'.binder.json').exists(),
        'binder_pin':read_json(Path(str(state)+'.binder.json')),
        'validator_pin_exists':Path(str(state)+'.validator.json').exists(),
        'validator_pin':read_json(Path(str(state)+'.validator.json')),
    }

def make(state,initialize,fault):
    return BinderBytePinnedBoundIssueLedger(
        state,
        binder_id=BINDER_ID,
        binder_source=ACTIVE_BINDER,
        validator_id=VALIDATOR_ID,
        validator_source=ACTIVE_VALIDATOR,
        initialize=initialize,
        fault=None if fault=='none' else fault,
    )

def reject(e,state,ledger=None):
    out={'status':'REJECTED','type':type(e).__name__,'error':str(e),**snapshot(state)}
    if ledger is not None:
        out['binder_sha256']=ledger.binder_sha256
        out['validator_sha256']=ledger.validator_sha256
        out['entries_in_memory']=ledger.entries
    return out

mode=sys.argv[1];state=Path(sys.argv[2]);initialize=sys.argv[3]=='1';fault=sys.argv[4]
try:
    ledger=make(state,initialize,fault)
    if mode=='init_only':
        out={'status':'INITIALIZED','binder_sha256':ledger.binder_sha256,'validator_sha256':ledger.validator_sha256,'entries_in_memory':ledger.entries,**snapshot(state)}
    elif mode=='issue':
        tok=ledger.issue(receipt(),terminal())
        out={'status':'ISSUED','token_id':tok.authority_end_id,'seq':tok.post_sequence,'binder_sha256':ledger.binder_sha256,'validator_sha256':ledger.validator_sha256,'entries_in_memory':ledger.entries,**snapshot(state)}
    elif mode=='recover':
        tok=ledger.recover_pending(RUNTIME_ID)
        out={'status':'RECOVERED','token_id':tok.authority_end_id,'seq':tok.post_sequence,'binder_sha256':ledger.binder_sha256,'validator_sha256':ledger.validator_sha256,'entries_in_memory':ledger.entries,**snapshot(state)}
    else:
        raise ValueError('unknown mode')
except Exception as e:
    out=reject(e,state,locals().get('ledger'))
print(json.dumps(out,sort_keys=True))
