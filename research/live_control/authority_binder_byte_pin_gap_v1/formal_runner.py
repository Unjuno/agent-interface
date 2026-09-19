from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent
WRAPPER=ROOT/'authority_bound_issue_api_v1'/'bound_authority_issue_v1.py'
BINDER=ROOT/'authority_end_identity_binding_v1'/'authority_end_identity_binding_v1.py'
V3=ROOT/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py'
V2=ROOT/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py'
BASE=ROOT/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py'
BRIDGE1=ROOT/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py'
DRIFT=H/'diagnostic_drift_binder.py'
WORKER=H/'process_worker.py'

EXPECTED={
    WRAPPER:'2f812a678b72f09985e24d003b2e7030508a49e4475e9d3aef5533b1a07f2ba2',
    BINDER:'a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730',
    V3:'a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5',
    V2:'f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9',
    BASE:'72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4',
    BRIDGE1:'2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e',
    DRIFT:'e75b6851f37525e6230cde448392a248edf78d10c3e38dc2aeba4a518384ad26',
    WORKER:'37a0e538a3956c9616d9e63f44b89d7a93868905df9af0bbf0bc45cc98b420da',
}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
for path,expected in EXPECTED.items():
    actual=sha(path)
    if actual!=expected: raise SystemExit(f'HASH_MISMATCH {path}: {actual} != {expected}')

RUNTIME_ID='runtime-intent-token'
FORGED_ID='caller-forged-id'
PIN_SHA=EXPECTED[V2]
rows=[]
def add(case,passed,detail): rows.append({'case':case,'pass':bool(passed),'detail':detail})

def copy_source(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(Path(src).read_bytes())

def entries_only(obj,expected): return obj.get('entries')==expected

with tempfile.TemporaryDirectory() as td:
    td=Path(td);sim=td/'sim';live=sim/'research'/'live_control';state=td/'token-state.json'
    mapping={
        WRAPPER:live/'authority_bound_issue_api_v1'/'bound_authority_issue_v1.py',
        BINDER:live/'authority_end_identity_binding_v1'/'authority_end_identity_binding_v1.py',
        V3:live/'authority_ended_validator_byte_binding_v3'/'validator_byte_pinned_ledger_v3.py',
        V2:live/'authority_ended_validator_byte_binding_v3'/'bridge_v2_semantic_snapshot.py',
        BASE:live/'authority_ended_restart_durability_v1'/'durable_token_state_v2.py',
        BRIDGE1:live/'authority_ended_restart_durability_v1'/'authority_ended_bridge_v1.py',
    }
    for src,dst in mapping.items(): copy_source(src,dst)
    active_binder=mapping[BINDER]
    nonbinder=[mapping[x] for x in [WRAPPER,V3,V2,BASE,BRIDGE1]]
    nonbinder_before={str(p.relative_to(sim)):sha(p) for p in nonbinder}

    env=os.environ.copy();env['SIM_ROOT']=str(sim)
    def worker(mode,arg):
        cp=subprocess.run([sys.executable,str(WORKER),mode,str(state),arg],env=env,text=True,capture_output=True)
        if cp.returncode!=0:
            raise RuntimeError(f'worker rc={cp.returncode} stdout={cp.stdout!r} stderr={cp.stderr!r}')
        lines=[line for line in cp.stdout.splitlines() if line.strip()]
        if len(lines)!=1: raise RuntimeError(f'unexpected worker output {cp.stdout!r}')
        return json.loads(lines[0])

    expected_one={RUNTIME_ID:{'post_sequence':11,'status':'pending'}}
    expected_two={RUNTIME_ID:{'post_sequence':11,'status':'pending'},FORGED_ID:{'post_sequence':11,'status':'pending'}}

    a=worker('issue','none')
    add('exact_binder_process_a_issues_runtime_id_only',a.get('status')=='ISSUED' and a.get('token_id')==RUNTIME_ID and a.get('seq')==11 and entries_only(a,expected_one),a)

    b=worker('issue','forged')
    add('exact_binder_control_restart_rejects_forged_id',b.get('status')=='REJECTED' and b.get('type')=='IdentityBindingError' and b.get('error')=='caller authority_end_id mismatch' and entries_only(b,expected_one),b)

    control_pin=b.get('validator_pin')
    copy_source(DRIFT,active_binder)
    drift_active_sha=sha(active_binder)
    nonbinder_during={str(p.relative_to(sim)):sha(p) for p in nonbinder}
    c=worker('issue','forged')
    add('drifted_binder_restart_admits_second_id_same_terminal',drift_active_sha==EXPECTED[DRIFT] and c.get('status')=='ISSUED' and c.get('token_id')==FORGED_ID and c.get('seq')==11 and entries_only(c,expected_two),{'active_binder_sha256':drift_active_sha,'worker':c})

    treatment_pin=c.get('validator_pin')
    pin_ok=(
        isinstance(control_pin,dict) and isinstance(treatment_pin,dict)
        and control_pin==treatment_pin
        and control_pin.get('validator_sha256')==PIN_SHA
        and control_pin.get('validator_id')=='bridge-v2-two-capture'
        and nonbinder_before==nonbinder_during
    )
    add('validator_pin_and_nonbinder_sources_unchanged',pin_ok,{'control_pin':control_pin,'treatment_pin':treatment_pin,'nonbinder_before':nonbinder_before,'nonbinder_during':nonbinder_during})

    copy_source(BINDER,active_binder)
    restored_sha=sha(active_binder)
    d=worker('recover',FORGED_ID)
    add('restored_exact_binder_cannot_remove_forged_pending_id',restored_sha==EXPECTED[BINDER] and d.get('status')=='RECOVERED' and d.get('token_id')==FORGED_ID and d.get('seq')==11 and entries_only(d,expected_two),{'restored_binder_sha256':restored_sha,'worker':d})

passed=len(rows)==5 and all(r['pass'] for r in rows)
out={
    'schema':'authority-binder-byte-pin-gap-v1-formal-result',
    'result_id':'authority-binder-byte-pin-gap-v1-20260916-01',
    'base_commit':'505d567ff269ecec3ac8ff81e35fc7816a787a6d',
    'rows':rows,
    'hard_gate_pass':passed,
    'decision':'RETAIN_BINDER_VERSION_GAP' if passed else 'REJECT_HYPOTHESIS',
    'formal_retries':0,
    'dependency_sha256':{p.name:sha(p) for p in EXPECTED},
    'source_sha256':{
        'formal_runner.py':sha(H/'formal_runner.py'),
        'process_worker.py':sha(WORKER),
        'diagnostic_drift_binder.py':sha(DRIFT),
    },
    'limitations':[
        'offline separate-process source-drift counterexample only',
        'diagnostic drift fixture is not a proposed implementation',
        'no hostile in-process isolation claim',
        'no live GUI/model/network/durable-submit',
        'PR #168 executed-source provenance remains independent',
    ],
}
(H/'formal-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 2)
