from __future__ import annotations
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent
CANDIDATE=ROOT/'authority_binder_byte_pin_v1'/'binder_byte_pinned_bound_issue_v1.py'
WORKER=H/'process_worker.py'
BINDER=ROOT/'authority_end_identity_binding_v1'/'authority_end_identity_binding_v1.py'
DRIFT_BINDER=ROOT/'authority_binder_byte_pin_gap_v1'/'diagnostic_drift_binder.py'
VALIDATOR=ROOT/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py'
DRIFT_VALIDATOR=H/'diagnostic_validator_byte_drift.py'
V3=ROOT/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py'
BASE=ROOT/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py'
BRIDGE1=ROOT/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py'
EXPECTED={
 CANDIDATE:'c725ca222920acf7dde9e5e0950a7178da92dbac41b49f65452acd0939241060',
 WORKER:'1ad0ca3937e361f1e4e2fd98921649a50b03361157709228fd650f9faf81834b',
 BINDER:'a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730',
 DRIFT_BINDER:'e75b6851f37525e6230cde448392a248edf78d10c3e38dc2aeba4a518384ad26',
 VALIDATOR:'f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9',
 DRIFT_VALIDATOR:'1f40ea48def2e99823c8e254dc1f95927d9c5600bfb3fc420185e76ca5f71a81',
 V3:'a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5',
 BASE:'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
 BRIDGE1:'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,e in EXPECTED.items():
 a=sha(p)
 if a!=e: raise SystemExit(f'HASH_MISMATCH {p}: {a} != {e}')

RUNTIME_ID='runtime-intent-token';BINDER_SHA=EXPECTED[BINDER];VALIDATOR_SHA=EXPECTED[VALIDATOR];DRIFT_VALIDATOR_SHA=EXPECTED[DRIFT_VALIDATOR]
rows=[]
def add(case,passed,detail): rows.append({'case':case,'pass':bool(passed),'detail':detail})
def cp(src,dst): dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(Path(src).read_bytes())
def rb(p): p=Path(p);return p.read_bytes() if p.exists() else None

def pin_bytes(state): return (rb(Path(str(state)+'.binder.json')),rb(Path(str(state)+'.validator.json')))
def state_bytes(state): return rb(state)

with tempfile.TemporaryDirectory() as td:
 td=Path(td);sim=td/'sim';live=sim/'research'/'live_control'
 mapping={
  CANDIDATE:live/'authority_binder_byte_pin_v1'/'binder_byte_pinned_bound_issue_v1.py',
  V3:live/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py',
  BASE:live/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py',
  BRIDGE1:live/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py',
 }
 for s,d in mapping.items(): cp(s,d)
 active_b=sim/'active_binder.py';active_v=sim/'active_validator.py'
 cp(BINDER,active_b);cp(VALIDATOR,active_v)
 env=os.environ.copy();env['SIM_ROOT']=str(sim)
 def run(mode,state,initialize,fault='none'):
  x=subprocess.run([sys.executable,str(WORKER),mode,str(state),'1' if initialize else '0',fault],env=env,text=True,capture_output=True)
  if x.returncode!=0: raise RuntimeError(f'worker rc={x.returncode} stdout={x.stdout!r} stderr={x.stderr!r}')
  ls=[z for z in x.stdout.splitlines() if z.strip()]
  if len(ls)!=1: raise RuntimeError(f'unexpected output {x.stdout!r}')
  return json.loads(ls[0])
 one={RUNTIME_ID:{'post_sequence':11,'status':'pending'}}

 # 1 baseline exact complete state.
 s1=td/'g1.json';cp(BINDER,active_b);cp(VALIDATOR,active_v);g1=run('issue',s1,True)
 add('baseline_exact_init_issue',g1.get('status')=='ISSUED' and g1.get('token_id')==RUNTIME_ID and g1.get('binder_sha256')==BINDER_SHA and g1.get('validator_sha256')==VALIDATOR_SHA and g1.get('entries_on_disk')==one,g1)

 # 2 binder sidecar only.
 s2=td/'g2.json';cp(BINDER,active_b);cp(VALIDATOR,active_v);g2=run('init_only',s2,True,'after_binder_sidecar')
 add('binder_sidecar_crash_leaves_no_validator_or_state',g2.get('status')=='REJECTED' and g2.get('type')=='InjectedBinderInitCrash' and g2.get('binder_pin_exists') is True and g2.get('validator_pin_exists') is False and g2.get('state_exists') is False,g2)

 # 3 no state existed, so an unpinned validator can become the initial validator choice.
 cp(DRIFT_VALIDATOR,active_v);g3=run('issue',s2,True)
 add('pre_state_unpinned_validator_can_become_initial_choice',g3.get('status')=='ISSUED' and g3.get('token_id')==RUNTIME_ID and g3.get('binder_sha256')==BINDER_SHA and g3.get('validator_sha256')==DRIFT_VALIDATOR_SHA and g3.get('validator_pin',{}).get('validator_sha256')==DRIFT_VALIDATOR_SHA and g3.get('entries_on_disk')==one,{'classification':'pre_state_initialization_choice','worker':g3})

 # 4 both pins, zero state via inner validator-sidecar crash.
 s4=td/'g4.json';cp(BINDER,active_b);cp(VALIDATOR,active_v);g4=run('init_only',s4,True,'after_sidecar')
 add('validator_sidecar_crash_leaves_both_pins_no_state',g4.get('status')=='REJECTED' and g4.get('type')=='InjectedInitCrash' and g4.get('binder_pin_exists') is True and g4.get('validator_pin_exists') is True and g4.get('state_exists') is False,g4)

 # 5 both pins exist: binder drift rejects without mutation.
 pre_pins=pin_bytes(s4);pre_state=state_bytes(s4);cp(DRIFT_BINDER,active_b);cp(VALIDATOR,active_v);g5=run('init_only',s4,True)
 add('both_pins_binder_drift_rejects_without_mutation',g5.get('status')=='REJECTED' and g5.get('type')=='BinderPinError' and g5.get('error')=='binder pin mismatch' and pin_bytes(s4)==pre_pins and state_bytes(s4)==pre_state,g5)

 # 6 both pins exist: validator drift rejects without mutation.
 cp(BINDER,active_b);cp(DRIFT_VALIDATOR,active_v);g6=run('init_only',s4,True)
 add('both_pins_validator_drift_rejects_without_mutation',g6.get('status')=='REJECTED' and g6.get('type')=='ValidatorPinError' and g6.get('error')=='validator pin mismatch' and pin_bytes(s4)==pre_pins and state_bytes(s4)==pre_state,g6)

 # 7 complete state: binder drift rejects without mutation.
 s7=td/'g7.json';cp(BINDER,active_b);cp(VALIDATOR,active_v);setup7=run('issue',s7,True);pre7=(state_bytes(s7),pin_bytes(s7));cp(DRIFT_BINDER,active_b);g7=run('recover',s7,False)
 add('complete_state_binder_drift_rejects_without_mutation',setup7.get('status')=='ISSUED' and g7.get('status')=='REJECTED' and g7.get('type')=='BinderPinError' and g7.get('error')=='binder pin mismatch' and (state_bytes(s7),pin_bytes(s7))==pre7,{'setup':setup7,'restart':g7})

 # 8 complete state: validator drift rejects without mutation.
 cp(BINDER,active_b);cp(DRIFT_VALIDATOR,active_v);g8=run('recover',s7,False)
 add('complete_state_validator_drift_rejects_without_mutation',g8.get('status')=='REJECTED' and g8.get('type')=='ValidatorPinError' and g8.get('error')=='validator pin mismatch' and (state_bytes(s7),pin_bytes(s7))==pre7,g8)

 # 9 state missing binder pin.
 s9=td/'g9.json';cp(BINDER,active_b);cp(VALIDATOR,active_v);setup9=run('issue',s9,True);state9=state_bytes(s9);vpin9=rb(Path(str(s9)+'.validator.json'));Path(str(s9)+'.binder.json').unlink();g9=run('recover',s9,False)
 add('existing_state_missing_binder_pin_rejects_without_mutation',setup9.get('status')=='ISSUED' and g9.get('status')=='REJECTED' and g9.get('type')=='BinderPinError' and g9.get('error')=='existing token state missing binder pin' and state_bytes(s9)==state9 and rb(Path(str(s9)+'.validator.json'))==vpin9 and not Path(str(s9)+'.binder.json').exists(),{'setup':setup9,'restart':g9})

 # 10 state missing validator pin.
 s10=td/'g10.json';cp(BINDER,active_b);cp(VALIDATOR,active_v);setup10=run('issue',s10,True);state10=state_bytes(s10);bpin10=rb(Path(str(s10)+'.binder.json'));Path(str(s10)+'.validator.json').unlink();g10=run('recover',s10,False)
 add('existing_state_missing_validator_pin_rejects_without_mutation',setup10.get('status')=='ISSUED' and g10.get('status')=='REJECTED' and g10.get('type')=='ValidatorPinError' and g10.get('error')=='existing token state missing validator pin' and state_bytes(s10)==state10 and rb(Path(str(s10)+'.binder.json'))==bpin10 and not Path(str(s10)+'.validator.json').exists(),{'setup':setup10,'restart':g10})

passed=len(rows)==10 and all(r['pass'] for r in rows)
out={
 'schema':'authority-split-pin-atomicity-v1-formal-result',
 'result_id':'authority-split-pin-atomicity-v1-20260916-01',
 'base_commit':'71dea2279dd4b8fb5a1d6f64e7c773a756feeb5b',
 'rows':rows,
 'hard_gate_pass':passed,
 'decision':'HOLD_COMPOSITE_MANIFEST_NO_STATE_REINTERPRETATION' if passed else 'RETAIN_SPLIT_PIN_ATOMICITY_GAP',
 'formal_retries':0,
 'dependency_sha256':{p.name:sha(p) for p in EXPECTED},
 'source_sha256':{'process_worker.py':sha(WORKER),'formal_runner.py':sha(H/'formal_runner.py'),'diagnostic_validator_byte_drift.py':sha(DRIFT_VALIDATOR)},
 'limitations':['restart-state continuity only; not external authorization of an allowed binder/validator pair','diagnostic validator differs from exact source only by trailing comment','offline separate-process only','no live GUI/model/network/durable-submit','PR #168 executed-source provenance remains independent'],
}
(H/'formal-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 2)
