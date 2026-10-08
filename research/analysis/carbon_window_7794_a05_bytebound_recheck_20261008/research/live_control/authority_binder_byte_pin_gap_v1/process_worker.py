from __future__ import annotations
import json,os,sys
from pathlib import Path

sim=Path(os.environ['SIM_ROOT']).resolve()
wrapper_dir=sim/'research'/'live_control'/'authority_bound_issue_api_v1'
if str(wrapper_dir) not in sys.path:
    sys.path.insert(0,str(wrapper_dir))
from bound_authority_issue_v1 import BoundAuthorityIssueLedger

RUNTIME_ID='runtime-intent-token'
FORGED_ID='caller-forged-id'
V2=sim/'research'/'live_control'/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py'

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
    if caller=='forged': out['authority_end_id']=FORGED_ID
    return out

def terminal():
    return {
        'status':'authority_ended',
        'interruption':{'intent_token':RUNTIME_ID,'record':{'reason':'expired','verified':True,'keys_down':[],'buttons_down':[]}},
        'release':{'intent_token':RUNTIME_ID,'verified':True,'keys_down':[],'buttons_down':[]},
    }

def snapshot(ledger,state):
    pin=json.loads(Path(str(state)+'.validator.json').read_text())
    return {'entries':ledger.entries,'validator_pin':pin}

mode=sys.argv[1]
state=Path(sys.argv[2])
ledger=BoundAuthorityIssueLedger(state,validator_id='bridge-v2-two-capture',validator_source=V2,initialize=not state.exists())
try:
    if mode=='issue':
        caller=sys.argv[3]
        tok=ledger.issue(receipt(caller),terminal())
        out={'status':'ISSUED','token_id':tok.authority_end_id,'seq':tok.post_sequence,**snapshot(ledger,state)}
    elif mode=='recover':
        rid=sys.argv[3]
        tok=ledger.recover_pending(rid)
        out={'status':'RECOVERED','token_id':tok.authority_end_id,'seq':tok.post_sequence,**snapshot(ledger,state)}
    else:
        raise ValueError('unknown mode')
except Exception as e:
    out={'status':'REJECTED','type':type(e).__name__,'error':str(e),**snapshot(ledger,state)}
print(json.dumps(out,sort_keys=True))
