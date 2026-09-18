from __future__ import annotations
import argparse,itertools,json,hashlib
from pathlib import Path
ACT=tuple(range(4));DOM=tuple(range(3));PAIRS=tuple(itertools.combinations(ACT,2))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=Path(a.output);assert not o.exists()
 bindings=list(itertools.product(DOM,repeat=4));cases=alias=disjoint=0
 for bind in bindings:
  for i,j in PAIRS:
   cases+=1
   if bind[i]==bind[j]:alias+=1
   else:disjoint+=1
 checks={'decision':r['decision']=='PASS_MULTI_ACTUATOR_STATE_DOMAIN_INDEPENDENCE_SCOPED','formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,
 'bindings':len(bindings)==r['bindings']==81,'cases':cases==r['cases']==486,'alias':alias==r['same_domain_cases']==162,'disjoint':disjoint==r['different_domain_cases']==324,
 'mismatch':r['candidate_oracle_mismatches']==0,'id_only_false_parallel':r['device_id_only_false_parallel_cases']==162,
 'witnesses':r['alias_missing_conflict_witnesses']==0 and r['sample_alias_witness'] is not None,'hidden_global':r['hidden_global_false_parallel'] is True,
 'corruptions':all(r['corruption_controls'].values()),'assumptions':r['assumptions']==['exclusive_state_domain_identity_complete','surfaces_otherwise_disjoint','no_other_shared_exclusive_resource','already_authorized_operations']}
 z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
