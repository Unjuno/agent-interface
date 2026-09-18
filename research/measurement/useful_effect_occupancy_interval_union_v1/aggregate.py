from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())

def main():
    d=ROOT/'formal_batches'
    ex=load(d/'exhaustive.json')
    bs=[load(d/f'bounded_{i}.json') for i in range(5)]
    ss=[load(d/f'stress_{i}.json') for i in range(5)]
    errors=[]
    if ex.get('kind')!='exhaustive':errors.append('exhaustive_kind')
    for i,x in enumerate(bs):
        if (x.get('kind'),x.get('index'),x.get('cases'))!=('bounded',i,100000):errors.append(f'bounded_{i}')
    for i,x in enumerate(ss):
        if (x.get('kind'),x.get('index'),x.get('cases'))!=('stress',i,20000):errors.append(f'stress_{i}')
    bounded=sum(x['cases'] for x in bs);stress=sum(x['cases'] for x in ss)
    old_mismatch=ex['old_mismatches']+sum(x['old_mismatches'] for x in bs)
    point_mismatch=ex['pointwise_mismatches']+sum(x['pointwise_mismatches'] for x in bs)
    inv=sum(x['invariant_errors'] for x in ss)
    result={
      'task':'USEFUL-EFFECT-OCCUPANCY-INTERVAL-UNION-20260918-001',
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'exhaustive_cases':ex['cases'],'bounded_random_cases':bounded,
      'bounded_pointwise_checked':sum(x['pointwise_checked'] for x in bs),
      'ns_stress_cases':stress,'bounded_old_set_mismatches':old_mismatch,
      'pointwise_oracle_mismatches':point_mismatch,'ns_invariant_errors':inv,
      'bounded_wall_s':sum(x['wall_s'] for x in bs),'exhaustive_wall_s':ex['wall_s'],
      'ns_stress_wall_s':sum(x['wall_s'] for x in ss),
      'ns_stress_peak_tracemalloc_bytes':max(x['peak_tracemalloc_bytes'] for x in ss),
      'parent_candidate_sha256':sha(ROOT/'parent_candidate.py'),
      'interval_candidate_sha256':sha(ROOT/'interval_candidate.py'),
      'batch_sha256':{'exhaustive':sha(d/'exhaustive.json'),
                      'bounded':[sha(d/f'bounded_{i}.json') for i in range(5)],
                      'stress':[sha(d/f'stress_{i}.json') for i in range(5)]},
      'errors':errors
    }
    result['decision']='PASS_OCCUPANCY_INTERVAL_UNION_EQUIVALENT_SCOPED' if not errors and bounded==500000 and stress==100000 and old_mismatch==0 and point_mismatch==0 and inv==0 else 'FAIL_OCCUPANCY_EQUIVALENCE'
    out=ROOT/'FORMAL_RESULT.json'
    if out.exists():raise SystemExit('FORMAL_RESULT exists')
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
