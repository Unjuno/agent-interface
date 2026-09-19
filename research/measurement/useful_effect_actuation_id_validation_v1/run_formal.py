from __future__ import annotations
import hashlib, json, random, sys, time
from pathlib import Path
from interval_contract import Actuation, EffectEvent, Interval, ReleaseReceipt, analyze
from id_validation import analyze_validated

ROOT=Path(__file__).resolve().parent
RESULT=ROOT/'FORMAL_RESULT.json'
if RESULT.exists():
    raise SystemExit('REFUSE_RERUN_RESULT_EXISTS')
VALID_SEED=96220260917001
MALFORMED_SEED=96220260917002
N_VALID=50_000
N_MALFORMED=50_000


def git_blob(path: Path) -> str:
    b=path.read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def rand_interval(rng, upper=180):
    s=rng.randrange(0,upper); e=rng.randrange(s,upper+1); return Interval(s,e)

def make_valid(case,rng):
    ws=rng.randrange(0,100); we=rng.randrange(ws,181); wait=Interval(ws,we)
    acts=[]
    n=rng.randrange(0,6)
    for i in range(n):
        aid=(f'動作-{case}-{i}' if (case+i)%17==0 else f'a-{case}-{i}')
        down=rng.randrange(0,151); lo=down+rng.randrange(0,16); hi=lo+rng.randrange(0,16)
        auth=[rand_interval(rng) for _ in range(rng.randrange(0,4))]
        acts.append(Actuation(down,ReleaseReceipt(lo,hi,False),auth,aid))
    ids=[a.actuation_id for a in acts]
    events=[]
    for j in range(rng.randrange(0,9)):
        choices=[None,f'unknown-{case}-{j}']+ids
        events.append(EffectEvent(rng.randrange(-20,221),rng.choice(choices),bool(rng.getrandbits(1)),bool(rng.getrandbits(1))))
    return wait,acts,events

BAD_HASHABLE=[None,'',0,False,1.5,b'x',('x',)]
BAD_EFFECT=['',0,False,1.5,b'x',('x',),['x'],{'x':1}]

def expect_reject(wait,acts,events):
    try: analyze_validated(wait,acts,events)
    except ValueError: return True
    return False

# Frozen predecessor defect controls.
W=Interval(0,100)
def A(aid): return Actuation(10,ReleaseReceipt(20,25,False),[Interval(0,100)],aid)
def E(aid): return EffectEvent(15,aid,True,True)
defects={}
for bad in (None,'',0):
    defects[repr(bad)]=analyze(W,[A(bad)],[E(bad)])['effects']['useful_bound']
if defects!={"None":1,"''":1,"0":1}: raise AssertionError(defects)

start=time.perf_counter_ns()
rng=random.Random(VALID_SEED)
valid_equal=0
for case in range(N_VALID):
    wait,acts,events=make_valid(case,rng)
    base=analyze(wait,acts,events)
    cand=analyze_validated(wait,acts,events)
    if base!=cand: raise AssertionError(('valid_regression',case,base,cand))
    valid_equal+=1

rng=random.Random(MALFORMED_SEED)
malformed_rejected=0
actuation_bad=0
effect_bad=0
for case in range(N_MALFORMED):
    wait=Interval(0,100)
    if case%2==0:
        bad=rng.choice(BAD_HASHABLE)
        acts=[A(bad)]
        events=[E(bad)]
        actuation_bad+=1
    else:
        bad=rng.choice(BAD_EFFECT)
        acts=[A(f'valid-{case}')]
        events=[E(bad)]
        effect_bad+=1
    if not expect_reject(wait,acts,events):
        raise AssertionError(('malformed_escape',case,repr(bad)))
    malformed_rejected+=1
elapsed=time.perf_counter_ns()-start

# Frozen controls after formal loops.
none_unbound=analyze_validated(W,[A('valid')],[E(None)])['effects']
unicode_equal=analyze(W,[A('動作-α')],[E('動作-α')])==analyze_validated(W,[A('動作-α')],[E('動作-α')])
duplicate_rejected=False
try: analyze_validated(W,[A('dup'),A('dup')],[])
except ValueError as e: duplicate_rejected='duplicate' in str(e)

result={
 'task':'USEFUL-EFFECT-ACTUATION-ID-VALIDATION-20260917-001',
 'base':'d994bc01a6a23d21bd565b84d58a43a99a562f89',
 'parent_git_blob':git_blob(ROOT/'interval_contract.py'),
 'parent_sha256':sha256(ROOT/'interval_contract.py'),
 'source_sha256':{n:sha256(ROOT/n) for n in ['PLAN.md','id_validation.py','test_static.py','run_formal.py','audit.py']},
 'formal_invocations':1,'formal_reruns':0,
 'valid_seed':VALID_SEED,'valid_cases':N_VALID,'valid_exact_equal':valid_equal,
 'malformed_seed':MALFORMED_SEED,'malformed_cases':N_MALFORMED,'malformed_rejected':malformed_rejected,
 'malformed_actuation_cases':actuation_bad,'malformed_effect_cases':effect_bad,
 'predecessor_defect_useful_bound':defects,
 'none_unbound_effects':none_unbound,
 'unicode_valid_equal':unicode_equal,
 'duplicate_valid_id_rejected':duplicate_rejected,
 'authority_actions':0,'task_input_actions':0,'network_actions':0,'model_calls':0,
 'elapsed_ns':elapsed,
 'disposition':'PASS_ACTUATION_ID_VALIDATION_SCOPED' if (valid_equal==N_VALID and malformed_rejected==N_MALFORMED and none_unbound['useful_unbound']==1 and none_unbound['useful_bound']==0 and unicode_equal and duplicate_rejected) else 'FAIL'
}
RESULT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,sort_keys=True))
