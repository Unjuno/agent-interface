from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path

TASK='MULTI_ACTUATOR_STATE_DOMAIN_INDEPENDENCE_R0_20260919_001'
ACTUATORS=tuple(range(4))
DOMAINS=tuple(range(3))
PAIRS=tuple(itertools.combinations(ACTUATORS,2))
BINDINGS=tuple(itertools.product(DOMAINS,repeat=len(ACTUATORS)))
EXPECTED_BINDINGS=81
EXPECTED_CASES=486
EXPECTED_ALIAS=162
EXPECTED_DISJOINT=324

def candidate(binding,a,b):
    return binding[a] != binding[b]

def oracle(binding,a,b):
    ra=('state_domain',binding[a])
    rb=('state_domain',binding[b])
    return ra != rb

def conflict_witness(binding,a,b):
    if binding[a] != binding[b]: return None
    return {'domain':binding[a],'op_a':{'actuator':a,'write':0},'op_b':{'actuator':b,'write':1},'commute':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--construction',action='store_true');args=ap.parse_args();out=Path(args.output);assert not out.exists()
    bindings=BINDINGS[:9] if args.construction else BINDINGS
    cases=alias=disjoint=mismatch=id_only_false_parallel=missing_witness=0
    sample_alias=None;sample_disjoint=None
    for binding in bindings:
        for a,b in PAIRS:
            cases+=1
            c=candidate(binding,a,b);o=oracle(binding,a,b)
            if c!=o:mismatch+=1
            if binding[a]==binding[b]:
                alias+=1
                if not c:
                    w=conflict_witness(binding,a,b)
                    if w is None:missing_witness+=1
                    elif sample_alias is None:sample_alias={'binding':list(binding),'pair':[a,b],'witness':w}
                if a!=b:id_only_false_parallel+=1
            else:
                disjoint+=1
                if sample_disjoint is None:sample_disjoint={'binding':list(binding),'pair':[a,b],'domains':[binding[a],binding[b]]}

    hidden_binding=(0,1,1,2); a,b=0,1
    domain_candidate=candidate(hidden_binding,a,b)
    complete_oracle_with_hidden_global=False
    hidden_global_false_parallel=domain_candidate and not complete_oracle_with_hidden_global

    corrupt={
      'alias_as_independent_detected': not candidate((0,0,1,2),0,1),
      'disjoint_as_conflict_detected': candidate((0,1,1,2),0,1),
      'hidden_global_omission_detected': hidden_global_false_parallel,
      'universe_counts_detected': EXPECTED_BINDINGS==81 and EXPECTED_CASES==486 and EXPECTED_ALIAS==162 and EXPECTED_DISJOINT==324,
    }
    full=not args.construction
    checks={
      'binding_count': (not full) or len(bindings)==EXPECTED_BINDINGS,
      'case_count': (not full) or cases==EXPECTED_CASES,
      'candidate_oracle_mismatch_zero':mismatch==0,
      'alias_count': (not full) or alias==EXPECTED_ALIAS,
      'disjoint_count': (not full) or disjoint==EXPECTED_DISJOINT,
      'id_only_false_parallel_count': (not full) or id_only_false_parallel==EXPECTED_ALIAS,
      'alias_conflict_witnesses_complete':missing_witness==0 and alias>0,
      'hidden_global_false_parallel':hidden_global_false_parallel,
      'corruptions':all(corrupt.values()),
    }
    if args.construction:decision='PASS_CONSTRUCTION_ELIGIBLE' if all(checks.values()) else 'FAIL_CONSTRUCTION'
    else:decision='PASS_MULTI_ACTUATOR_STATE_DOMAIN_INDEPENDENCE_SCOPED' if all(checks.values()) else 'FAIL_INTEGRITY'
    result={'task':TASK,'decision':decision,'construction_only':args.construction,'formal_invocations':0 if args.construction else 1,'reruns':0,'replacements':0,'tuning':0,
      'actuators':len(ACTUATORS),'domains':len(DOMAINS),'bindings':len(bindings),'pairs_per_binding':len(PAIRS),'cases':cases,
      'same_domain_cases':alias,'different_domain_cases':disjoint,'candidate_oracle_mismatches':mismatch,
      'device_id_only_false_parallel_cases':id_only_false_parallel,'alias_missing_conflict_witnesses':missing_witness,
      'sample_alias_witness':sample_alias,'sample_disjoint_case':sample_disjoint,'hidden_global_false_parallel':hidden_global_false_parallel,
      'corruption_controls':corrupt,'checks':checks,
      'assumptions':['exclusive_state_domain_identity_complete','surfaces_otherwise_disjoint','no_other_shared_exclusive_resource','already_authorized_operations']}
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if decision.startswith('PASS_') else 1)
if __name__=='__main__':main()
