from __future__ import annotations
from itertools import combinations
import hashlib,json,argparse
from pathlib import Path
from candidate import required_decision,assume_complete,complete_only,PROVEN_COMPLETE,PARTIAL,UNKNOWN

TASK='OBSERVATION-GATING-O3-RELEVANCE-COMPLETENESS-20260918-001'
N=6
U=frozenset(range(N))


def subsets():
    xs=range(N)
    for r in range(N+1):
        for c in combinations(xs,r):
            yield frozenset(c)


def analytic_witness():
    A=(0,1); x=2
    visible=('s0',7,11,A,(x,),())
    return {
        'inputs_identical': True,
        'required_decisions_differ': True,
        'w0_required':'SUPPRESS',
        'w1_required':'FORWARD',
        'w0_visible':visible,
        'w1_visible':visible,
        'x_outside_declared':x not in A,
    }


def run(source_sha256:dict)->dict:
    m={
      'rows':0,
      'unsafe_false_suppressions':0,
      'unsafe_true_suppressions':0,
      'complete_only_false_suppressions_truthful':0,
      'complete_only_true_suppressions_truthful':0,
      'partial_suppressions':0,
      'unknown_suppressions':0,
      'forged_complete_false_suppressions':0,
      'stale_suppressions':0,
    }
    digest=hashlib.sha256(); examples=[]
    for true_rel in subsets():
      for declared in subsets():
        for x in range(N):
          changed=frozenset({x})
          for critical in (frozenset(),frozenset({x})):
            required=required_decision(set(true_rel),set(critical),set(changed))
            unsafe=assume_complete(set(declared),set(critical),set(changed),True)
            m['rows']+=1
            if unsafe=='SUPPRESS' and required=='FORWARD':
                m['unsafe_false_suppressions']+=1
                if len(examples)<8:
                    examples.append({'true':sorted(true_rel),'declared':sorted(declared),'x':x,'critical':sorted(critical)})
            if unsafe=='SUPPRESS' and required=='SUPPRESS': m['unsafe_true_suppressions']+=1

            coverage=PROVEN_COMPLETE if declared==true_rel else PARTIAL
            cand=complete_only(set(declared),set(critical),set(changed),coverage,True)
            if cand=='SUPPRESS' and required=='FORWARD': m['complete_only_false_suppressions_truthful']+=1
            if cand=='SUPPRESS' and required=='SUPPRESS': m['complete_only_true_suppressions_truthful']+=1
            partial=complete_only(set(declared),set(critical),set(changed),PARTIAL,True)
            unknown=complete_only(set(declared),set(critical),set(changed),UNKNOWN,True)
            m['partial_suppressions']+=int(partial=='SUPPRESS')
            m['unknown_suppressions']+=int(unknown=='SUPPRESS')
            forged=complete_only(set(declared),set(critical),set(changed),PROVEN_COMPLETE,True)
            if forged=='SUPPRESS' and required=='FORWARD': m['forged_complete_false_suppressions']+=1
            stale=complete_only(set(declared),set(critical),set(changed),PROVEN_COMPLETE,False)
            m['stale_suppressions']+=int(stale=='SUPPRESS')
            row=[sorted(true_rel),sorted(declared),x,sorted(critical),required,unsafe,cand,partial,unknown,forged,stale]
            digest.update(json.dumps(row,separators=(',',':')).encode())
    return {
      'task':TASK,'phase':'formal','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'source_sha256':source_sha256,'analytic':analytic_witness(),'metrics':m,
      'ledger_sha256':digest.hexdigest(),'examples':examples,
    }


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-manifest',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    sm=json.loads(Path(a.source_manifest).read_text())
    r=run(sm['sha256'])
    Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'metrics':r['metrics'],'ledger_sha256':r['ledger_sha256']},sort_keys=True))
if __name__=='__main__':main()
