from __future__ import annotations
import copy, hashlib, importlib, importlib.util, json, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
LIVE=HERE.parent
DUR=LIVE/'authority_ended_restart_durability_v1'
ABI=LIVE/'inkscape_authority_ended_abi_v2'
FORMAL=ABI/'formal-evidence.json'
TOKEN=DUR/'durable_token_state_v2.py'
BRIDGE1=DUR/'authority_ended_bridge_v1.py'
BRIDGE2=ABI/'authority_ended_bridge_v2.py'
EXPECTED={
 TOKEN:'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
 BRIDGE1:'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
 BRIDGE2:'37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52',
}
for p,h in EXPECTED.items():
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=h: raise AssertionError(f'source mismatch {p}: {got} != {h}')

def load_bridge2():
    spec=importlib.util.spec_from_file_location('authority_ended_bridge_v2_exact',BRIDGE2)
    m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m); return m

def load_token():
    for name in ('durable_token_state_v2','authority_ended_bridge_v1'):
        sys.modules.pop(name,None)
    sys.path.insert(0,str(DUR))
    try: return importlib.import_module('durable_token_state_v2')
    finally: sys.path.pop(0)

def truthful_receipt():
    f=json.loads(FORMAL.read_text())
    terminal=f['terminal']; release=terminal['release']; post=terminal['post_authority_observation']
    stopped=f['input_stopped']['stopped_ns']
    post_admissions=sum(1 for e in f['input_events'] if e.get('admitted_ns',0)>stopped)
    return {
      'terminal_status':terminal['status'],
      'release_verified':release['verified'],
      'keys_down':release['keys_down'],'buttons_down':release['buttons_down'],
      'post_release_input_admissions':post_admissions,
      'steps_completed':terminal['steps_completed'],
      'post_authority':copy.deepcopy(post),
    }
rows=[]
def add(case,ok,detail): rows.append({'case':case,'pass':bool(ok),'detail':detail})
receipt=truthful_receipt()
# A: unchanged durable ledger + unchanged bridge-v1.
m=load_token()
with tempfile.TemporaryDirectory(prefix='abi-token-current-') as td:
    ledger=m.DurableTokenLedger(Path(td)/'token.json',initialize=True)
    try: ledger.issue(copy.deepcopy(receipt)); a='UNEXPECTED_ISSUE'
    except Exception as e: a={'type':type(e).__name__,'error':str(e)}
    add('current_v2_ledger_rejects_truthful_two_capture_receipt',a=={'type':'AuthorityEndedNotReady','error':'exactly one passive post-authority capture required'},a)
# B-E: same token state machine, only its imported decision function is swapped in-memory to exact current bridge-v2.
m=load_token(); b2=load_bridge2(); m.to_caller_execution_decision=b2.to_caller_execution_decision
with tempfile.TemporaryDirectory(prefix='abi-token-bridge2-') as td:
    path=Path(td)/'token.json'; ledger=m.DurableTokenLedger(path,initialize=True)
    try: ledger.issue(copy.deepcopy(receipt)); b='UNEXPECTED_ISSUE'
    except Exception as e: b={'type':type(e).__name__,'error':str(e)}
    add('bridge_v2_exposes_missing_runtime_authority_end_id',b=={'type':'StateError','error':'runtime authority_end_id required'},b)
    diagnostic=copy.deepcopy(receipt); diagnostic['authority_end_id']='diagnostic-synthetic-authority-end-id'
    token=ledger.issue(diagnostic)
    add('diagnostic_id_allows_single_issue',token.authority_end_id==diagnostic['authority_end_id'] and token.post_sequence==11 and ledger.entries[token.authority_end_id]['status']=='pending',{'id':token.authority_end_id,'post_sequence':token.post_sequence,'status':ledger.entries[token.authority_end_id]['status']})
    try: ledger.issue(diagnostic); d='UNEXPECTED_REISSUE'
    except Exception as e: d={'type':type(e).__name__,'error':str(e)}
    add('diagnostic_duplicate_rejected',d=={'type':'DuplicateReceipt','error':'authority_end_id already exists'},d)
    restarted=m.DurableTokenLedger(path); recovered=restarted.recover_pending(diagnostic['authority_end_id'])
    add('diagnostic_pending_recovers_after_restart',recovered.authority_end_id==diagnostic['authority_end_id'] and recovered.post_sequence==11,{'id':recovered.authority_end_id,'post_sequence':recovered.post_sequence,'status':restarted.entries[recovered.authority_end_id]['status']})
passed=len(rows)==5 and all(r['pass'] for r in rows)
result={
 'schema':'inkscape-authority-durable-token-compat-v1-result',
 'upstream_authority_abi_head':'d1c7d0531993b23a61c7f38e12d979c27948cf6e',
 'rows':rows,'hard_gate_pass':passed,
 'decision':'RETAIN_COMPOSITION_GAP' if passed else 'RETAIN_FAILURE',
 'source_sha256':{str(p.relative_to(LIVE)):h for p,h in EXPECTED.items()},
 'formal_evidence_sha256':hashlib.sha256(FORMAL.read_bytes()).hexdigest(),
 'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'limits':['offline interface audit','diagnostic synthetic authority_end_id only','no durable-submit transport','no GUI/model/network'],
}
print(json.dumps(result,indent=2,sort_keys=True))
