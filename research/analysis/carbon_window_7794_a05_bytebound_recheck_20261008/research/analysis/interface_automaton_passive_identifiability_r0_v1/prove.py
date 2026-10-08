from __future__ import annotations
import argparse, collections, hashlib, itertools, json
from pathlib import Path

TASK='INTERFACE-AUTOMATON-PASSIVE-IDENTIFIABILITY-R0-20260919-001'
N_STATES=3; N_ACTIONS=2; N_ENTRIES=N_STATES*N_ACTIONS
AUTOMATA=tuple(itertools.product(range(N_STATES), repeat=N_ENTRIES))
MASKS=tuple(range(1<<N_ENTRIES))

def popcount(x): return x.bit_count()
def signature(auto,mask): return tuple(auto[i] for i in range(N_ENTRIES) if mask>>i & 1)

def eval_masks(masks):
    mask_rows=[]; class_errors=0; incomplete_singletons=0; full_ambiguous=0
    for mask in masks:
        groups=collections.Counter(signature(a,mask) for a in AUTOMATA)
        k=popcount(mask); expected_classes=N_STATES**k; expected_size=N_STATES**(N_ENTRIES-k)
        sizes=set(groups.values())
        ok=(len(groups)==expected_classes and sizes=={expected_size})
        if not ok: class_errors+=1
        if k<N_ENTRIES and any(v==1 for v in groups.values()): incomplete_singletons+=1
        if k==N_ENTRIES and any(v!=1 for v in groups.values()): full_ambiguous+=1
        mask_rows.append({'mask':mask,'observed_pairs':k,'class_count':len(groups),'expected_class_count':expected_classes,'class_size_values':sorted(sizes),'expected_class_size':expected_size,'pass':ok})
    return mask_rows,class_errors,incomplete_singletons,full_ambiguous

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--construction',action='store_true');a=ap.parse_args();out=Path(a.output);assert not out.exists()
    masks=(0,31,63) if a.construction else MASKS
    rows,class_errors,incomplete_singletons,full_ambiguous=eval_masks(masks)
    amb_mask=31; auto_a=(0,0,0,0,0,0);auto_b=(0,0,0,0,0,1)
    ambiguity={'mask':amb_mask,'automaton_a':list(auto_a),'automaton_b':list(auto_b),'same_observed_signature':signature(auto_a,amb_mask)==signature(auto_b,amb_mask),'different_unobserved_entry':auto_a[5]!=auto_b[5],'unobserved_entry':5}
    corrupt={
      'k5_not_unique': 3**(6-5)>1,
      'observed_change_changes_signature': signature((1,0,0,0,0,0),1)!=signature((0,0,0,0,0,0),1),
      'unobserved_not_impossible': ambiguity['same_observed_signature'] and ambiguity['different_unobserved_entry'],
      'universe_counts': len(AUTOMATA)==729 and len(MASKS)==64,
    }
    full=not a.construction
    checks={
      'automata_count':len(AUTOMATA)==729,
      'mask_count':(not full) or len(masks)==64,
      'class_formula_all':class_errors==0,
      'no_incomplete_singleton':incomplete_singletons==0,
      'full_coverage_unique':full_ambiguous==0,
      'explicit_ambiguity':all(ambiguity[k] for k in ('same_observed_signature','different_unobserved_entry')),
      'corruptions':all(corrupt.values()),
    }
    decision=('PASS_CONSTRUCTION_ELIGIBLE' if a.construction else 'PASS_PASSIVE_AUTOMATON_COVERAGE_IDENTIFIABILITY_SCOPED') if all(checks.values()) else ('FAIL_CONSTRUCTION' if a.construction else 'FAIL_INTEGRITY')
    result={'task':TASK,'decision':decision,'construction_only':a.construction,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,
      'states':N_STATES,'actions':N_ACTIONS,'table_entries':N_ENTRIES,'automata_count':len(AUTOMATA),'coverage_masks':len(masks),'mask_rows':rows,
      'class_formula_errors':class_errors,'incomplete_coverage_singleton_classes':incomplete_singletons,'full_coverage_ambiguous_classes':full_ambiguous,
      'ambiguity_witness':ambiguity,'corruption_controls':corrupt,'checks':checks,
      'assumptions':['deterministic','stationary','directly_observed_state_labels','directly_observed_action_labels','complete_declared_state_action_domain']}
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['decision','automata_count','coverage_masks','class_formula_errors','incomplete_coverage_singleton_classes','full_coverage_ambiguous_classes','ambiguity_witness','digest']},indent=2,sort_keys=True))
    raise SystemExit(0 if decision.startswith('PASS_') else 1)
if __name__=='__main__':main()
