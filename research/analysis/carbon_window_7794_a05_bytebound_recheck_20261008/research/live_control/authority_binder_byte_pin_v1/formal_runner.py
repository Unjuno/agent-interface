from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent
CANDIDATE=H/'binder_byte_pinned_bound_issue_v1.py'
WORKER=H/'process_worker.py'
BINDER=ROOT/'authority_end_identity_binding_v1'/'authority_end_identity_binding_v1.py'
DRIFT=ROOT/'authority_binder_byte_pin_gap_v1'/'diagnostic_drift_binder.py'
V3=ROOT/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py'
V2=ROOT/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py'
BASE=ROOT/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py'
BRIDGE1=ROOT/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py'

EXPECTED={
    CANDIDATE:'c725ca222920acf7dde9e5e0950a7178da92dbac41b49f65452acd0939241060',
    WORKER:'0cdc84b6089779096b51d0e983be9cf724bb9640d13b7b48aa7bce39b3cb8fee',
    BINDER:'a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730',
    DRIFT:'e75b6851f37525e6230cde448392a248edf78d10c3e38dc2aeba4a518384ad26',
    V3:'a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5',
    V2:'f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9',
    BASE:'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
    BRIDGE1:'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
for path,expected in EXPECTED.items():
    actual=sha(path)
    if actual!=expected:
        raise SystemExit(f'HASH_MISMATCH {path}: {actual} != {expected}')

RUNTIME_ID='runtime-intent-token'
FORGED_ID='caller-forged-id'
BINDER_ID='authority-end-intent-token-v1'
BINDER_SHA=EXPECTED[BINDER]
VALIDATOR_SHA=EXPECTED[V2]
rows=[]
def add(case,passed,detail): rows.append({'case':case,'pass':bool(passed),'detail':detail})

def copy_source(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(Path(src).read_bytes())

def raw_bytes(path):
    p=Path(path)
    return p.read_bytes() if p.exists() else None

with tempfile.TemporaryDirectory() as td:
    td=Path(td);sim=td/'sim';live=sim/'research'/'live_control'
    mapping={
        CANDIDATE:live/'authority_binder_byte_pin_v1'/'binder_byte_pinned_bound_issue_v1.py',
        V3:live/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py',
        V2:live/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py',
        BASE:live/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py',
        BRIDGE1:live/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py',
    }
    for src,dst in mapping.items(): copy_source(src,dst)
    active=sim/'active_binder.py';copy_source(BINDER,active)
    drift=sim/'diagnostic_drift_binder.py';copy_source(DRIFT,drift)
    env=os.environ.copy();env['SIM_ROOT']=str(sim)

    def worker(args):
        cp=subprocess.run([sys.executable,str(WORKER),*map(str,args)],env=env,text=True,capture_output=True)
        if cp.returncode!=0:
            raise RuntimeError(f'worker rc={cp.returncode} stdout={cp.stdout!r} stderr={cp.stderr!r}')
        lines=[x for x in cp.stdout.splitlines() if x.strip()]
        if len(lines)!=1: raise RuntimeError(f'unexpected worker stdout {cp.stdout!r}')
        return json.loads(lines[0])

    def exact_pin(obj):
        pin=obj.get('binder_pin') or {}
        return pin=={
            'schema':'authority-end-identity-binder-byte-pin-v1',
            'binder_id':BINDER_ID,
            'binder_sha256':BINDER_SHA,
            'function_name':'bind_authority_end_identity',
        }

    # Gate 1: exact initialization + issue.
    s1=td/'gate1.json'
    g1=worker(['issue',s1,'1','none','none','none'])
    one={RUNTIME_ID:{'post_sequence':11,'status':'pending'}}
    add('exact_init_pins_binder_and_issues_runtime_id',
        g1.get('status')=='ISSUED' and g1.get('token_id')==RUNTIME_ID and g1.get('seq')==11
        and g1.get('binder_sha256')==BINDER_SHA and g1.get('validator_sha256')==VALIDATOR_SHA
        and g1.get('entries_on_disk')==one and exact_pin(g1),g1)

    # Gate 2: candidate loaded exact binder, then disk source changes; loaded behavior stays exact.
    copy_source(BINDER,active)
    before_state=raw_bytes(s1)
    g2=worker(['loaded_drift_issue',s1,'0','none',drift,'forged'])
    add('post_constructor_source_replacement_does_not_change_loaded_binder',
        g2.get('status')=='REJECTED' and g2.get('type')=='IdentityBindingError'
        and g2.get('error')=='caller authority_end_id mismatch' and g2.get('binder_sha256')==BINDER_SHA
        and g2.get('entries_on_disk')==one and raw_bytes(s1)==before_state,g2)

    # Gate 3: fresh process under drift bytes fails at binder pin before issue/state change.
    drift_sha=sha(active)
    before_state=raw_bytes(s1);before_binder_pin=raw_bytes(Path(str(s1)+'.binder.json'));before_validator_pin=raw_bytes(Path(str(s1)+'.validator.json'))
    g3=worker(['issue',s1,'0','none','forged','none'])
    add('fresh_restart_under_drift_rejects_pin_mismatch_without_mutation',
        drift_sha==EXPECTED[DRIFT] and g3.get('status')=='REJECTED' and g3.get('type')=='BinderPinError'
        and g3.get('error')=='binder pin mismatch' and raw_bytes(s1)==before_state
        and raw_bytes(Path(str(s1)+'.binder.json'))==before_binder_pin
        and raw_bytes(Path(str(s1)+'.validator.json'))==before_validator_pin,g3)

    # Gate 4: restoring exact bytes reopens/recover pending.
    copy_source(BINDER,active)
    g4=worker(['recover',s1,'0','none',RUNTIME_ID])
    add('restore_exact_binder_reopens_and_recovers_pending',
        g4.get('status')=='RECOVERED' and g4.get('token_id')==RUNTIME_ID and g4.get('seq')==11
        and g4.get('binder_sha256')==BINDER_SHA and g4.get('entries_on_disk')==one,g4)

    # Gate 5: crash after binder sidecar, no inner state; exact retry completes.
    s5=td/'gate5.json';copy_source(BINDER,active)
    g5a=worker(['init_only',s5,'1','after_binder_sidecar'])
    no_inner=(not g5a.get('state_exists') and not g5a.get('validator_pin_exists') and g5a.get('binder_pin_exists') and exact_pin(g5a))
    g5b=worker(['issue',s5,'1','none','none','none'])
    add('binder_sidecar_crash_exact_retry_completes',
        g5a.get('status')=='REJECTED' and g5a.get('type')=='InjectedBinderInitCrash' and g5a.get('error')=='after_binder_sidecar'
        and no_inner and g5b.get('status')=='ISSUED' and g5b.get('token_id')==RUNTIME_ID
        and g5b.get('entries_on_disk')==one and exact_pin(g5b),{'crash':g5a,'retry':g5b})

    # Gate 6: same crash then drift source rejects before token/validator state creation.
    s6=td/'gate6.json';copy_source(BINDER,active)
    g6a=worker(['init_only',s6,'1','after_binder_sidecar'])
    copy_source(DRIFT,active)
    binder_pin_before=raw_bytes(Path(str(s6)+'.binder.json'))
    g6b=worker(['init_only',s6,'1','none'])
    add('binder_sidecar_crash_then_drift_rejects_before_inner_state',
        g6a.get('status')=='REJECTED' and g6a.get('type')=='InjectedBinderInitCrash'
        and g6b.get('status')=='REJECTED' and g6b.get('type')=='BinderPinError' and g6b.get('error')=='binder pin mismatch'
        and not Path(s6).exists() and not Path(str(s6)+'.validator.json').exists()
        and raw_bytes(Path(str(s6)+'.binder.json'))==binder_pin_before,{'crash':g6a,'drift_retry':g6b})
    copy_source(BINDER,active)

    # Gate 7: existing token state without binder pin fails closed and state is unchanged.
    s7=td/'gate7.json'
    g7a=worker(['issue',s7,'1','none','none','none'])
    state_before=raw_bytes(s7);validator_before=raw_bytes(Path(str(s7)+'.validator.json'))
    Path(str(s7)+'.binder.json').unlink()
    g7b=worker(['recover',s7,'0','none',RUNTIME_ID])
    add('existing_state_missing_binder_pin_fails_closed',
        g7a.get('status')=='ISSUED' and g7b.get('status')=='REJECTED' and g7b.get('type')=='BinderPinError'
        and g7b.get('error')=='existing token state missing binder pin' and raw_bytes(s7)==state_before
        and raw_bytes(Path(str(s7)+'.validator.json'))==validator_before and not Path(str(s7)+'.binder.json').exists(),{'setup':g7a,'missing_pin_restart':g7b})

    # Gate 8: delegated token-state crash semantics remain intact.
    s8=td/'gate8.json';copy_source(BINDER,active)
    g8a=worker(['issue',s8,'1','none','none','after_replace_fsync'])
    g8b=worker(['recover',s8,'0','none',RUNTIME_ID])
    add('delegated_after_replace_fsync_crash_recovers_runtime_pending',
        g8a.get('status')=='REJECTED' and g8a.get('type')=='InjectedCrash' and g8a.get('error')=='after_replace_fsync'
        and g8b.get('status')=='RECOVERED' and g8b.get('token_id')==RUNTIME_ID and g8b.get('seq')==11
        and g8b.get('entries_on_disk')==one and exact_pin(g8b),{'crash':g8a,'restart':g8b})

passed=len(rows)==8 and all(r['pass'] for r in rows)
out={
    'schema':'authority-binder-byte-pin-v1-formal-result',
    'result_id':'authority-binder-byte-pin-v1-20260916-01',
    'base_commit':'7bea48e69cfb62b2993e7d7ea18a1688d527b70b',
    'rows':rows,
    'hard_gate_pass':passed,
    'decision':'RETAIN_BINDER_BYTE_PIN_V1' if passed else 'RETAIN_FAILURE',
    'formal_retries':0,
    'dependency_sha256':{p.name:sha(p) for p in EXPECTED},
    'source_sha256':{
        'binder_byte_pinned_bound_issue_v1.py':sha(CANDIDATE),
        'process_worker.py':sha(WORKER),
        'formal_runner.py':sha(H/'formal_runner.py'),
    },
    'limitations':[
        'pins binder provenance/consistency, not semantic approval of arbitrary first-initialization binder',
        'binder and validator pins are separate sidecars, not one atomic composite manifest',
        'offline separate-process semantics only',
        'no live GUI/model/network/durable-submit',
        'PR #168 executed-source provenance remains independent',
    ],
}
(H/'formal-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 2)
