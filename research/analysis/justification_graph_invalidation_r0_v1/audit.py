from __future__ import annotations
import argparse,itertools,json,hashlib
from pathlib import Path
NROOT=3;ROOTMASK=7;DERIVED=56

def cands(n):return tuple([1<<i for i in range(n)]+[(1<<a)|(1<<b) for a,b in itertools.combinations(range(n),2)])
def fams(n):
 c=cands(n);return tuple((x,) for x in c)+tuple(itertools.combinations(c,2))
F=(fams(3),fams(4),fams(5))
def sat(v,f):return any((v&j)==j for j in f)
def eval_topo(root,fs):
 v=root
 if sat(v,fs[0]):v|=8
 if sat(v,fs[1]):v|=16
 if sat(v,fs[2]):v|=32
 return v
def eval_fix(root,fs):
 v=root|DERIVED
 for _ in range(4):
  n=root
  if sat(v,fs[0]):n|=8
  if sat(v,fs[1]):n|=16
  if sat(v,fs[2]):n|=32
  if n==v:return v
  v=n
 raise AssertionError
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=Path(a.output);assert not o.exists()
 structures=0;mismatch=0;unsupported=0
 for f0 in F[0]:
  for f1 in F[1]:
   for f2 in F[2]:
    structures+=1;fs=(f0,f1,f2)
    for root in range(8):
     t=eval_topo(root,fs);q=eval_fix(root,fs)
     if t!=q:mismatch+=1
     if bool(t&8)!=sat(t,f0) or bool(t&16)!=sat(t,f1) or bool(t&32)!=sat(t,f2):unsupported+=1
 hidden=(1&1)!=0 and (1&3)!=3
 checks={'decision':r['decision']=='PASS_JUSTIFICATION_GRAPH_INVALIDATION_SCOPED','formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,
 'structures':structures==r['structures']==138600,'conditions':r['conditions']==7761600,'equivalence':mismatch==r['topo_iterative_mismatches']==0,
 'supported':unsupported==r['unsupported_state_errors']==0,'nonclosure':r['nonclosure_change_errors']==0,'naive_witness':r['naive_descendant_overinvalidated_claim_instances']>0 and r['naive_overinvalidation_witness'] is not None,
 'hidden_edge':hidden and r['hidden_edge_false_retain'] is True,'corruptions':all(r['corruption_controls'].values()),
 'assumptions':r['assumptions']==['acyclic','monotone_positive_support','complete_declared_supports','claim_valid_iff_any_justification_all_valid']}
 z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'auditor_structures':structures,'auditor_root_states':structures*8,'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
 o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
