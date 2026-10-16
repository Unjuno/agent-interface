from __future__ import annotations
import copy, hashlib, json, platform, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from post_authority_observation_v1 import AuthorityEndPreconditionError, build_authority_ended_receipt
from authority_ended_bridge_v1 import AuthorityEndedNotReady, to_caller_execution_decision

class Clock:
    def __init__(self, ns): self.ns=ns
    def __call__(self): return self.ns
    def advance(self, ns): self.ns += ns

class Backend:
    def __init__(self, clock, *, sequence=5, delay_ns=100_000_000, advance=True, fail=False):
        self.clock=clock; self.sequence=sequence; self.delay_ns=delay_ns; self.advance=advance; self.fail=fail; self.snapshot_calls=0
    def snapshot(self, identifier, index):
        self.snapshot_calls += 1
        if self.snapshot_calls > 1: raise AssertionError('more than one snapshot')
        self.clock.advance(self.delay_ns)
        if self.fail: raise RuntimeError('injected snapshot failure')
        if self.advance: self.sequence += 1

BASE_RELEASE={'verified':True,'keys_down':[],'buttons_down':[],'verified_ns':1_000_000_000}
BUDGET=400_000_000
SOURCE_SEQUENCE=5

def bridge(receipt):
    try: return {'accepted':True,'decision':to_caller_execution_decision(receipt)}
    except AuthorityEndedNotReady as exc: return {'accepted':False,'error':str(exc)}

def build(*,release=None,admissions=0,budget=BUDGET,delay=100_000_000,advance=True,fail=False):
    clock=Clock(1_000_000_000); backend=Backend(clock,delay_ns=delay,advance=advance,fail=fail)
    try:
        receipt=build_authority_ended_receipt(backend,identifier='expire-hold',index=0,release=copy.deepcopy(BASE_RELEASE if release is None else release),steps_completed=0,source_sequence=SOURCE_SEQUENCE,lifecycle_budget_ns=budget,post_release_input_admissions=admissions,clock_ns=clock)
        return {'kind':'receipt','receipt':receipt,'bridge':bridge(receipt),'snapshot_calls':backend.snapshot_calls}
    except AuthorityEndPreconditionError as exc:
        return {'kind':'precondition_reject','error':str(exc),'snapshot_calls':backend.snapshot_calls}

rows=[]
def add(case, ok, detail): rows.append({'case':case,'pass':bool(ok),'detail':detail})
clean=build(); add('clean_receipt_accepted', clean['kind']=='receipt' and clean['snapshot_calls']==1 and clean['bridge']=={'accepted':True,'decision':{'status':'safe_yield','reason':'authority_unavailable','completed_actions':0}} and clean['receipt']['post_authority']['captures']==1 and clean['receipt']['post_authority']['sequence']==6, clean)
late=build(delay=500_000_000); add('late_snapshot_rejected', late['kind']=='receipt' and late['snapshot_calls']==1 and late['receipt']['post_authority']['within_lifecycle_deadline'] is False and late['bridge']=={'accepted':False,'error':'post-authority observation outside lifecycle deadline'}, late)
failed=build(fail=True,delay=50_000_000); add('snapshot_exception_rejected', failed['kind']=='receipt' and failed['snapshot_calls']==1 and failed['receipt']['post_authority']['captures']==0 and failed['bridge']=={'accepted':False,'error':'exactly one passive post-authority capture required'}, failed)
stale=build(advance=False); add('nonadvancing_sequence_rejected', stale['kind']=='receipt' and stale['snapshot_calls']==1 and stale['receipt']['post_authority']['sequence_advanced'] is False and stale['bridge']=={'accepted':False,'error':'post-authority observation must advance sequence'}, stale)
admission=build(admissions=1); add('post_release_admission_rejected_before_snapshot', admission['kind']=='precondition_reject' and admission['snapshot_calls']==0 and admission['error']=='zero post-release input admissions required', admission)
unverified=build(release={'verified':False,'keys_down':[],'buttons_down':[],'verified_ns':1_000_000_000}); add('unverified_release_rejected_before_snapshot', unverified['kind']=='precondition_reject' and unverified['snapshot_calls']==0 and unverified['error']=='verified release required before post-authority capture', unverified)
dirty=build(release={'verified':True,'keys_down':['Shift_L'],'buttons_down':[],'verified_ns':1_000_000_000}); add('dirty_release_rejected_before_snapshot', dirty['kind']=='precondition_reject' and dirty['snapshot_calls']==0 and dirty['error']=='empty released input state required', dirty)
bad_budget=build(budget=0); add('nonpositive_budget_rejected_before_snapshot', bad_budget['kind']=='precondition_reject' and bad_budget['snapshot_calls']==0 and bad_budget['error']=='positive lifecycle budget required', bad_budget)
mut=copy.deepcopy(clean['receipt']); mut['post_authority']['captures']=2; mut_result=bridge(mut); add('two_capture_mutation_rejected', clean['snapshot_calls']==1 and mut_result=={'accepted':False,'error':'exactly one passive post-authority capture required'}, {'bridge':mut_result,'snapshot_calls_from_clean_source':clean['snapshot_calls']})
max_calls=max(r['detail'].get('snapshot_calls',r['detail'].get('snapshot_calls_from_clean_source',0)) for r in rows)
passed=len(rows)==9 and all(r['pass'] for r in rows) and max_calls<=1
result={
 'schema':'inkscape-authority-ended-candidate-v1-result',
 'base_commit':'7f42fd577dff98d6a27a8eceb79d86bee0358bf9',
 'rows':rows,
 'hard_gate_pass':passed,
 'max_snapshot_calls_any_case':max_calls,
 'decision':'PASS_OFFLINE_RECEIPT_MECHANISM' if passed else 'RETAIN_FAILURE',
 'candidate_sha256':hashlib.sha256((ROOT/'post_authority_observation_v1.py').read_bytes()).hexdigest(),
 'bridge_sha256':hashlib.sha256((ROOT/'authority_ended_bridge_v1.py').read_bytes()).hexdigest(),
 'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'environment':{'python':sys.version.split()[0],'platform':platform.platform()},
 'limits':['deterministic fake backend','injectable monotonic ns clock','no live GUI','no model','no OS input','no network'],
}
print(json.dumps(result,indent=2,sort_keys=True))
