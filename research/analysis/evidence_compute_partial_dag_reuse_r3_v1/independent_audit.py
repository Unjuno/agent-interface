#!/usr/bin/env python3
import itertools,json,hashlib
from pathlib import Path
E=3;N=4

def dags():
    opts=[list(range(1,2**(E+i))) for i in range(N)]
    return itertools.product(*opts)

def dirty_by_edges(dag,changed):
    state={('e',e):bool(changed&(1<<e)) for e in range(E)}
    for i,parents in enumerate(dag):
        d=False
        for bit in range(E+i):
            if not (parents&(1<<bit)):continue
            key=('e',bit) if bit<E else ('n',bit-E)
            if state[key]:d=True;break
        state[('n',i)]=d
    return tuple(state[('n',i)] for i in range(N))

def projection_witness_exists(dag,changed,target):
    # Backward reachability implemented independently, no transitive closure reuse.
    stack=[('n',target)];seen=set()
    while stack:
        kind,x=stack.pop()
        if (kind,x) in seen:continue
        seen.add((kind,x))
        if kind=='e':
            if changed&(1<<x):return True
            continue
        pm=dag[x]
        for bit in range(E+x):
            if pm&(1<<bit):stack.append(('e',bit) if bit<E else ('n',bit-E))
    return False

def main():
    root=Path(__file__).parent;r=json.loads((root/'RESULT.json').read_text());errs=[]
    dc={str(i):0 for i in range(N+1)};cases=0;dirty_total=0;strict=0;directmiss=0;unsafe=0;necessity=0
    emask=(1<<E)-1
    dagcount=0
    for dag in dags():
        dagcount+=1
        for changed in range(1,1<<E):
            cases+=1;o=dirty_by_edges(dag,changed);n=sum(o);dc[str(n)]+=1;dirty_total+=n
            if n<N:strict+=1
            direct=[bool(pm&emask&changed) for pm in dag]
            directmiss+=sum(1 for a,b in zip(direct,o) if b and not a)
            unsafe+=n
            for i,d in enumerate(o):
                if d:
                    if not projection_witness_exists(dag,changed,i):errs.append('necessity');raise SystemExit(3)
                    necessity+=1
    checks={
      'dags':dagcount==r['labelled_dags']==205065,
      'cases':cases==r['cases']==1435455,
      'dirty_hist':dc==r['dirty_count_histogram'],
      'dirty_total':dirty_total==r['dirty_nodes_total'],
      'strict':strict==r['strict_partial_rebuild_cases'] and strict>0,
      'direct':directmiss==r['direct_only_missed_descendants'] and directmiss>0,
      'unsafe':unsafe==r['all_reuse_unsafe_nodes'] and unsafe>0,
      'necessity':necessity==r['necessity_witnesses'] and r['necessity_missing']==0,
      'parents':r['parent_blobs']=={'decision_lattice_result':'529c3939b5ff4ac58ce71b7dad9d06e1409d64c8','exact_reuse_report':'acb545678ac80da917d80bb40fedd8f84624ae92'},
      'decision':r['decision']=='PASS_PARTIAL_DAG_RECOMPUTATION_BOUND_SCOPED',
    }
    errs=[k for k,v in checks.items() if not v]
    out={'pass':not errs,'errors':errs,'checks':checks,'result_sha256':hashlib.sha256((root/'RESULT.json').read_bytes()).hexdigest()}
    (root/'INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(bool(errs))
if __name__=='__main__':main()
