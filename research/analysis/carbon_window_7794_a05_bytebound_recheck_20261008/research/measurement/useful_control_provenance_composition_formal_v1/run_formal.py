from __future__ import annotations
import hashlib, json, random, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
MEAS=HERE.parent
sys.path.insert(0,str(MEAS/'useful_control_interval_contract_v1'))
sys.path.insert(0,str(MEAS/'useful_control_provenance_composition_v1'))
sys.path.insert(0,str(HERE))
from interval_contract import Actuation, EffectEvent, Interval, ReleaseReceipt
from composed_contract import EffectRecord, analyze_composed
from oracle import oracle_analyze

RESULT=HERE/'FORMAL_RESULT.json'
if RESULT.exists():
    raise SystemExit('REFUSE_RERUN_RESULT_EXISTS')
VALID_SEED=96320260917011
ADVERSARIAL_SEED=96320260917012
N_VALID=100_000
N_ADVERSARIAL=50_000
EXPECTED_COMPOSITION_BLOB='b78ced2ca877b7c8ba28ec093c531ad4d2cbb73a'
EXPECTED_PARENT_BLOB='979f257b4f02be80bcaa30ae8d5a0aa92162bfb1'

def git_blob(path: Path) -> str:
    b=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def assert_source_identity():
    c=MEAS/'useful_control_provenance_composition_v1'/'composed_contract.py'
    p=MEAS/'useful_control_interval_contract_v1'/'interval_contract.py'
    assert git_blob(c)==EXPECTED_COMPOSITION_BLOB,(git_blob(c),EXPECTED_COMPOSITION_BLOB)
    assert git_blob(p)==EXPECTED_PARENT_BLOB,(git_blob(p),EXPECTED_PARENT_BLOB)

def rand_interval(rng: random.Random, hi: int=96) -> Interval:
    s=rng.randrange(0,hi)
    e=rng.randrange(s,hi+1)
    return Interval(s,e)

def make_valid_case(case: int, rng: random.Random):
    ws=rng.randrange(0,96)
    we=rng.randrange(ws+1,97)
    wait=Interval(ws,we)
    acts=[]
    for i in range(rng.randrange(0,6)):
        aid=(f' id-{case}-{i} ' if (case+i)%23==0 else (f'動作-{case}-{i}' if (case+i)%19==0 else f'a-{case}-{i}'))
        down=rng.randrange(0,91)
        lo=rng.randrange(down,min(96,down+8)+1)
        hi=rng.randrange(lo,min(96,lo+8)+1)
        auth=[rand_interval(rng) for _ in range(rng.randrange(0,4))]
        acts.append(Actuation(down,ReleaseReceipt(lo,hi,False),auth,aid))
    ids=[a.actuation_id for a in acts]
    records=[]
    for j in range(rng.randrange(0,10)):
        eid=(f' effect-{case}-{j} ' if (case+j)%29==0 else f'e-{case}-{j}')
        lineage_choices=[None,f'unknown-{case}-{j}']+ids
        lineage=rng.choice(lineage_choices)
        t=rng.randrange(-6,111)
        records.append(EffectRecord(eid,EffectEvent(t,lineage,bool(rng.getrandbits(1)),bool(rng.getrandbits(1)))))
    return wait,acts,records

def invoke_candidate(wait,acts,records):
    try:
        return ('ok',analyze_composed(wait,acts,records))
    except ValueError as e:
        return ('error',str(e))

def make_adversarial_case(case: int, rng: random.Random):
    k=case%10
    W=Interval(0,40)
    def A(aid='a',down=10):
        return Actuation(down,ReleaseReceipt(20,24,False),[Interval(5,18)],aid)
    def R(eid='e',t=12,lineage='a',scored=True,useful=True):
        return EffectRecord(eid,EffectEvent(t,lineage,scored,useful))
    if k==0:
        bad=rng.choice([None,'','   ',0,False,b'x'])
        return W,[A(bad)],[R('',-3,'',True,True)]
    if k==1:
        return W,[A('dup'),A('dup')],[R('',-3,'',True,True)]
    if k==2:
        bad=rng.choice(['','   ',0,False,b'x'])
        return W,[A('a')],[R(bad,-3,'',True,True)]
    if k==3:
        return W,[A('a')],[R('same',-3,'',True,True),R('same',-4,' ',True,True)]
    if k==4:
        return W,[A('a')],[R('e',-3,'   ',True,True)]
    if k==5:
        return W,[A('a')],[R('e',-3,'a',False,True)]
    if k==6:
        return W,[A('a',down=10)],[R('e',9,'a',False,True)]
    if k==7:
        return W,[A('a',down=10)],[R('e',9,'a',True,True)]
    if k==8:
        return W,[A('a')],[R('e',12,'missing',True,True)]
    return W,[A('a')],[R('e',12,'missing',True,False)]

def boundary_controls():
    W=Interval(0,30)
    A=Actuation(10,ReleaseReceipt(15,18,False),[Interval(8,13)],'a')
    cases={
        'exact_at_down':[EffectRecord('e',EffectEvent(10,'a',True,True))],
        'post_release':[EffectRecord('e',EffectEvent(25,'a',True,True))],
        'negative_unscored':[EffectRecord('e',EffectEvent(-1,'a',False,True))],
        'positive_predown_unscored':[EffectRecord('e',EffectEvent(9,'a',False,True))],
        'unknown_useful':[EffectRecord('e',EffectEvent(12,'missing',True,True))],
        'unknown_nonuseful':[EffectRecord('e',EffectEvent(12,'missing',True,False))],
        'identity_before_negative':[EffectRecord('e',EffectEvent(-1,'   ',True,True))],
    }
    passed=0
    for records in cases.values():
        exp=oracle_analyze(W,[A],records)
        got=invoke_candidate(W,[A],records)
        assert got==exp,(records,got,exp)
        passed+=1
    error_cases=[
        ([Actuation(10,ReleaseReceipt(15,18,False),[],'   ')],[],('error','invalid actuation_id')),
        ([A,A],[],('error','duplicate actuation_id')),
        ([A],[EffectRecord('   ',EffectEvent(12,'a',True,True))],('error','invalid effect_id')),
        ([A],[EffectRecord('x',EffectEvent(12,'a',True,True)),EffectRecord('x',EffectEvent(13,'a',True,True))],('error','duplicate effect_id')),
    ]
    for acts,records,exp in error_cases:
        got=invoke_candidate(W,acts,records)
        assert got==exp,(got,exp)
        assert oracle_analyze(W,acts,records)==exp
        passed+=1
    return passed

assert_source_identity()
controls_passed=boundary_controls()
start=time.perf_counter_ns()
rng=random.Random(VALID_SEED)
valid_equal=0
for case in range(N_VALID):
    wait,acts,records=make_valid_case(case,rng)
    expected=oracle_analyze(wait,acts,records)
    assert expected[0]=='ok'
    got=invoke_candidate(wait,acts,records)
    if got!=expected:
        raise AssertionError(('valid_mismatch',case,got,expected))
    valid_equal+=1
rng=random.Random(ADVERSARIAL_SEED)
adversarial_equal=0
adversarial_error=0
adversarial_ok=0
for case in range(N_ADVERSARIAL):
    wait,acts,records=make_adversarial_case(case,rng)
    expected=oracle_analyze(wait,acts,records)
    got=invoke_candidate(wait,acts,records)
    if got!=expected:
        raise AssertionError(('adversarial_mismatch',case,got,expected))
    if expected[0]=='error': adversarial_error+=1
    else: adversarial_ok+=1
    adversarial_equal+=1
elapsed=time.perf_counter_ns()-start
source_names=['PLAN.md','oracle.py','construction.py','run_formal.py','audit.py','corruption_controls.py']
result={
    'task':'USEFUL-CONTROL-PROVENANCE-COMPOSITION-FORMAL-20260917-001',
    'base':'592427d8f70efafed5819acec123f3fd0efa485b',
    'composition_git_blob':git_blob(MEAS/'useful_control_provenance_composition_v1'/'composed_contract.py'),
    'composition_sha256':sha256(MEAS/'useful_control_provenance_composition_v1'/'composed_contract.py'),
    'parent_git_blob':git_blob(MEAS/'useful_control_interval_contract_v1'/'interval_contract.py'),
    'parent_sha256':sha256(MEAS/'useful_control_interval_contract_v1'/'interval_contract.py'),
    'source_sha256':{n:sha256(HERE/n) for n in source_names},
    'formal_invocations':1,'formal_reruns':0,
    'valid_seed':VALID_SEED,'valid_cases':N_VALID,'valid_exact_equal':valid_equal,
    'adversarial_seed':ADVERSARIAL_SEED,'adversarial_cases':N_ADVERSARIAL,'adversarial_exact_equal':adversarial_equal,
    'adversarial_error_cases':adversarial_error,'adversarial_role_cases':adversarial_ok,
    'boundary_controls_passed':controls_passed,
    'boundary_controls_total':11,
    'model_calls':0,'network_actions':0,'task_input_actions':0,'authority_actions':0,
    'elapsed_ns':elapsed,
    'disposition':'PASS_USEFUL_CONTROL_PROVENANCE_COMPOSITION_SCOPED' if (valid_equal==N_VALID and adversarial_equal==N_ADVERSARIAL and controls_passed==11) else 'FAIL'
}
RESULT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,sort_keys=True))
