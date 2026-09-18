from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_count(T,n,d):
    if T<=0 or n<=0 or d<=0: raise ValueError
    x=n*d-(n-1)*T
    if x<=0: return 0
    if x>=T: return T
    return x


def audit(result_path=None):
    result_path=Path(result_path) if result_path else ROOT/'RESULT.json'
    result=json.loads(result_path.read_text())
    schedule=json.loads((ROOT/'schedule.json').read_text())
    errors=[]
    if result.get('period_ns') != schedule['period_ns']: errors.append('period')
    if result.get('schedule_sha256') != sha(ROOT/'schedule.json'): errors.append('schedule_hash')
    if result.get('invocation') != {'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}: errors.append('invocation')
    expected={(c['attempts'],c['span_ns']):c for c in schedule['cases']}
    seen=set()
    for row in result.get('rows',[]):
        key=(row.get('attempts'),row.get('span_ns'))
        if key not in expected or key in seen: errors.append(f'row_key:{key}'); continue
        seen.add(key)
        T=schedule['period_ns']; n=row['attempts']; d=row['span_ns']
        want=independent_count(T,n,d)
        if row.get('exact_failure_phase_count') != want: errors.append(f'exact:{key}')
        if row.get('closed_form_failure_phase_count') != want: errors.append(f'closed:{key}')
        ints=row.get('failure_intervals',[])
        card=0; last=-1
        for pair in ints:
            if not isinstance(pair,list) or len(pair)!=2: errors.append(f'interval_shape:{key}'); continue
            lo,hi=pair
            if not (0<=lo<=hi<T): errors.append(f'interval_bounds:{key}')
            if lo<=last: errors.append(f'interval_overlap:{key}')
            card += hi-lo+1; last=hi
        if card != want: errors.append(f'interval_cardinality:{key}')
        if bool(row.get('guaranteed')) != (want==0): errors.append(f'guaranteed:{key}')
    if seen != set(expected): errors.append('row_coverage')
    for n in [2,3,4]:
        b=((n-1)*schedule['period_ns'])//n
        plus=[r for r in result['rows'] if r['attempts']==n and r['span_ns']==b+1]
        if len(plus)!=1 or plus[0]['exact_failure_phase_count']<=0: errors.append(f'plus1:{n}')
    n2=[r for r in result['rows'] if r['attempts']==2 and r['span_ns']==r['boundary_ns']+1]
    if len(n2)!=1 or n2[0]['exact_failure_phase_count']!=1: errors.append('predecessor_1ns_control')
    if result.get('method_disagreements') != 0: errors.append('method_disagreements')
    if result.get('gate_errors') != []: errors.append('gate_errors')
    expected_decision='PASS_EXACT_COHERENCE_PHASE_GEOMETRY_SCOPED' if not errors else result.get('decision')
    if not errors and result.get('decision') != expected_decision: errors.append('decision')
    return errors

if __name__=='__main__':
    errors=audit()
    out={'decision':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','errors':errors}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
    if errors: raise SystemExit(2)
