from __future__ import annotations
import copy,hashlib,json,sys,tempfile
from pathlib import Path
H=Path(__file__).resolve().parent; ROOT=H.parent
WRAPPER=ROOT/'authority_binder_byte_pin_v1'/'binder_byte_pinned_bound_issue_v1.py'
BINDER=ROOT/'authority_end_identity_binding_v1'/'authority_end_identity_binding_v1.py'
VALIDATOR=ROOT/'inkscape_authority_ended_abi_v2'/'authority_ended_bridge_v2.py'
V3=ROOT/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py'
BASE=ROOT/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py'
BRIDGE1=ROOT/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py'
LIVE=ROOT/'inkscape_abi_v2_source_first_live_v1'/'formal-result.json'
for p in [ROOT/'authority_binder_byte_pin_v1',ROOT/'authority_end_identity_binding_v1',ROOT/'authority_ended_validator_byte_binding_v3',ROOT/'authority_ended_restart_durability_v1']:
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from binder_byte_pinned_bound_issue_v1 import BinderBytePinnedBoundIssueLedger
EXPECTED={
 LIVE:'402f6320f7a87acd0540b9aab1cd2eee610fab73c9937c72a682b77f11e0e9f3',
 WRAPPER:'c725ca222920acf7dde9e5e0950a7178da92dbac41b49f65452acd0939241060',
 BINDER:'a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730',
 VALIDATOR:'37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52',
 V3:'a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5',
 BASE:'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
 BRIDGE1:'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
actual={p:sha(p) for p in EXPECTED}
if any(actual[p]!=e for p,e in EXPECTED.items()):
    raise SystemExit('SOURCE_OR_INPUT_HASH_MISMATCH '+repr({str(p):[actual[p],e] for p,e in EXPECTED.items() if actual[p]!=e}))
live=json.loads(LIVE.read_text());RID='901e6ed15b87454fdbef7909c1e0f026';SEQ=3
receipt=live['receipt'];terminal=live['terminal']
rows=[]
def add(case,passed,detail): rows.append({'case':case,'pass':bool(passed),'detail':detail})
def reject(fn):
    try: fn(); return {'status':'UNEXPECTED_PASS'}
    except Exception as e: return {'status':'REJECTED','type':type(e).__name__,'error':str(e)}
def loadj(p): return json.loads(Path(p).read_text())
input_ok=(live.get('pass') is True and live.get('formal_retries')==0 and live.get('authority_end_id')==RID and receipt.get('authority_end_id')==RID and terminal.get('interruption',{}).get('intent_token')==RID and terminal.get('release',{}).get('intent_token')==RID and receipt.get('post_authority',{}).get('sequence')==SEQ)
add('exact_live_input_and_dependency_identities',input_ok and all(actual[p]==e for p,e in EXPECTED.items()),{'result_id':live.get('result_id'),'authority_end_id':live.get('authority_end_id'),'sequence':receipt.get('post_authority',{}).get('sequence'),'source_sha256':{p.name:actual[p] for p in EXPECTED}})
with tempfile.TemporaryDirectory() as td:
    state=Path(td)/'token-state.json';rb=copy.deepcopy(receipt);tb=copy.deepcopy(terminal)
    led=BinderBytePinnedBoundIssueLedger(state,binder_id='authority-end-intent-token-v1',binder_source=BINDER,validator_id='inkscape-authority-ended-abi-v2-current',validator_source=VALIDATOR,initialize=True)
    tok=led.issue(receipt,terminal)
    expected_pending={RID:{'post_sequence':SEQ,'status':'pending'}}
    add('issue_exact_runtime_identity_without_caller_mutation',tok.authority_end_id==RID and tok.post_sequence==SEQ and receipt==rb and terminal==tb and led.entries==expected_pending,{'token_id':tok.authority_end_id,'post_sequence':tok.post_sequence,'entries':led.entries,'receipt_unchanged':receipt==rb,'terminal_unchanged':terminal==tb})
    bpin=loadj(Path(str(state)+'.binder.json'));vpin=loadj(Path(str(state)+'.validator.json'))
    add('sidecars_pin_exact_live_policy_bytes',bpin.get('binder_sha256')==EXPECTED[BINDER] and bpin.get('binder_id')=='authority-end-intent-token-v1' and vpin.get('validator_sha256')==EXPECTED[VALIDATOR] and vpin.get('validator_id')=='inkscape-authority-ended-abi-v2-current',{'binder_pin':bpin,'validator_pin':vpin})
    led2=BinderBytePinnedBoundIssueLedger(state,binder_id='authority-end-intent-token-v1',binder_source=BINDER,validator_id='inkscape-authority-ended-abi-v2-current',validator_source=VALIDATOR)
    rt=led2.recover_pending(RID)
    add('fresh_reopen_recovers_exact_pending_live_token',rt.authority_end_id==RID and rt.post_sequence==SEQ and led2.entries==expected_pending,{'token_id':rt.authority_end_id,'post_sequence':rt.post_sequence,'entries':led2.entries})
    before=copy.deepcopy(led2.entries);dup=reject(lambda:led2.issue(receipt,terminal))
    add('duplicate_live_receipt_rejects_without_mutation',dup.get('type')=='DuplicateReceipt' and led2.entries==before==expected_pending,{'rejection':dup,'entries':led2.entries})
    forged=copy.deepcopy(receipt);forged['authority_end_id']='caller-forged-live-id';before=copy.deepcopy(led2.entries);bad=reject(lambda:led2.issue(forged,terminal))
    add('forged_live_identity_rejects_before_mutation',bad.get('type')=='IdentityBindingError' and bad.get('error')=='caller authority_end_id mismatch' and led2.entries==before==expected_pending,{'rejection':bad,'entries':led2.entries})
    led2.consume(rt);led3=BinderBytePinnedBoundIssueLedger(state,binder_id='authority-end-intent-token-v1',binder_source=BINDER,validator_id='inkscape-authority-ended-abi-v2-current',validator_source=VALIDATOR);consumed=reject(lambda:led3.recover_pending(RID));expected_consumed={RID:{'post_sequence':SEQ,'status':'consumed'}}
    add('consume_restart_preserves_consumed_live_identity',consumed.get('type')=='TokenConsumed' and led3.entries==expected_consumed,{'rejection':consumed,'entries':led3.entries})
passed=len(rows)==7 and all(x['pass'] for x in rows)
out={'schema':'inkscape-live-receipt-durable-composition-v1-formal-result','result_id':'inkscape-live-receipt-durable-composition-v1-20260916-01','base_commit':'0792fe8bbacb53073b7f818244b0bf52f9c20fe6','input_result_id':live.get('result_id'),'input_result_sha256':actual[LIVE],'rows':rows,'hard_gate_pass':passed,'decision':'RETAIN_LIVE_RECEIPT_DURABLE_IDENTITY_COMPOSITION' if passed else 'RETAIN_FAILURE','formal_retries':0,'source_sha256':{p.name:actual[p] for p in EXPECTED},'runner_sha256':sha(H/'formal_runner.py'),'limitations':['offline replay of exact retained live evidence','does not prove full live servo/executor durable write in same process','no durable-submit/network/crash-after-send/external exactly-once claim']}
(H/'formal-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 2)
