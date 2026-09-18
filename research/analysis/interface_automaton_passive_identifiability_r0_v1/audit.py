from __future__ import annotations
import argparse, collections, hashlib, itertools, json
from pathlib import Path
N=3;E=6;AUTOS=tuple(itertools.product(range(N),repeat=E))
def sig(a,m):return tuple(a[i] for i in range(E) if m>>i&1)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=Path(a.output);assert not o.exists()
 errors=0; classes_by_k={}
 for m in range(64):
  g=collections.Counter(sig(x,m) for x in AUTOS);k=m.bit_count();sizes=set(g.values())
  if len(g)!=3**k or sizes!={3**(6-k)}:errors+=1
  classes_by_k.setdefault(str(k),set()).add((len(g),tuple(sorted(sizes))))
 checks={'decision':r['decision']=='PASS_PASSIVE_AUTOMATON_COVERAGE_IDENTIFIABILITY_SCOPED','formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,
 'automata':len(AUTOS)==r['automata_count']==729,'masks':r['coverage_masks']==64,'formula':errors==r['class_formula_errors']==0,
 'incomplete_no_singleton':r['incomplete_coverage_singleton_classes']==0,'full_unique':r['full_coverage_ambiguous_classes']==0,
 'ambiguity':r['ambiguity_witness']['same_observed_signature'] and r['ambiguity_witness']['different_unobserved_entry'],'corruptions':all(r['corruption_controls'].values()),
 'assumptions':r['assumptions']==['deterministic','stationary','directly_observed_state_labels','directly_observed_action_labels','complete_declared_state_action_domain']}
 z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'auditor_formula_errors':errors,'classes_by_observed_count':{k:[list(x) for x in sorted(v)] for k,v in classes_by_k.items()},'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
 o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
