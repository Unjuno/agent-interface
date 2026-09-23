import argparse, json
from pathlib import Path

def expected(rows):
    if type(rows) is not int or rows<=0 or rows%6: return None
    n=rows//6
    return {
      'candidate_oracle_mismatch':0,
      'candidate_stale_critical_joins':0,
      'candidate_cross_identity_generation_joins':0,
      'candidate_malformed_missing_future_joins':0,
      'valid_candidate_joins':2*n,
      'valid_candidate_joins_rejected_by_strict':n,
      'naive_stale_critical_joins':n,
      'critical_expiry_rows':n,
      'identity_generation_mismatch_rows':2*n,
      'malformed_missing_future_rows':n,
      'category_counts':{
        'VALID_SKEW':n,'CRITICAL_EXPIRED':n,'IDENTITY_MISMATCH':n,
        'MALFORMED':n,'VALID_STRICT':n,'GENERATION_MISMATCH':n
      }
    }

def expected_decision(rows):
    if rows==300000: return 'PASS_OBSERVATION_EPOCH_BOUNDED_SKEW_R1_SCOPED'
    return 'PASS_CONSTRUCTION_ELIGIBLE'

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); rows=r.get('metrics',{}).get('rows'); exp=expected(rows)
    errors=[]
    if exp is None: errors.append('row_shape')
    else:
        for k,v in exp.items():
            if r['metrics'].get(k)!=v: errors.append(k)
    if r.get('directed')!={
      'focus_mutation':{'candidate':False,'naive':True,'oracle':False},
      'valid_stagger':{'candidate':True,'strict':False,'oracle':True}
    }: errors.append('directed')
    if r.get('decision')!=expected_decision(rows): errors.append('decision')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errors.append('counters')
    out={'pass':not errors,'errors':sorted(errors),'method':'closed-form category-count audit; imports no experiment implementation'}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['pass'] else 5)
