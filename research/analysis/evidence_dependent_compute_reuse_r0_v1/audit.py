from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
N=4;STATES=tuple(range(1<<N));SUBSETS=tuple(range(1<<N))
def size(mask): return mask.bit_count()
def eq(a,b,d): return ((a^b)&d)==0
def bit(s,i): return (s>>i)&1

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=Path(a.output);assert not o.exists()
    exact=mismatch=disc=0
    for d in SUBSETS:
        for s in STATES:
            for c in STATES:
                if eq(s,c,d): exact+=1
                else:
                    mismatch+=1
                    changed=(s^c)&d;i=(changed&-changed).bit_length()-1
                    if bit(s,i)==bit(c,i): disc+=1
    hidden=0;hidden_bad=0
    for d in SUBSETS:
        for h in range(N):
            if d>>h&1: continue
            hidden+=1
            if not (eq(0,1<<h,d) and bit(0,h)!=bit(1<<h,h)): hidden_bad+=1
    checks={
      'decision':r['decision']=='PASS_EXACT_DEPENDENCY_VERSION_REUSE_SCOPED',
      'formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,
      'total':r['total_cases']==4096,
      'exact':exact==r['exact_projection_pairs']==1296,
      'mismatch':mismatch==r['mismatched_projection_pairs']==2800,
      'discriminators':disc==r['mismatch_discriminator_failures']==0,
      'hidden':hidden==r['hidden_dependency_controls']==32 and hidden_bad==r['hidden_dependency_failures']==0,
      'empty':r['empty_dependency_pairs']==256,
      'corruptions':all(r['corruption_controls'].values()),
      'assumptions':r['assumptions']==['deterministic_pure_job','complete_declared_dependencies','non_reused_semantic_version_identity'],
    }
    z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
    o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
