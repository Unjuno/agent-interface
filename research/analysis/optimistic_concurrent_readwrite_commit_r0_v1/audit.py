from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def independent_expected():
    c = {
        'rows':0,'oracle_parallel':0,'oracle_serialize':0,'oracle_revalidate':0,
        'global_false_serializations':0,'write_only_unsafe_parallel':0,
        'hazard_rows_stale_read':0,'hazard_rows_a_write_b_read':0,
        'hazard_rows_b_write_a_read':0,'hazard_rows_ww':0,
    }
    for ra in range(16):
      for wa in range(16):
       for rb in range(16):
        for wb in range(16):
         for changed in range(16):
          c['rows'] += 1
          stale = bool((ra|rb)&changed)
          ww = bool(wa&wb)
          awbr = bool(wa&rb)
          bwar = bool(wb&ra)
          c['hazard_rows_stale_read'] += stale
          c['hazard_rows_ww'] += ww
          c['hazard_rows_a_write_b_read'] += awbr
          c['hazard_rows_b_write_a_read'] += bwar
          if stale:
              verdict='revalidate'
          elif ww or awbr or bwar:
              verdict='serialize'
          else:
              verdict='parallel'
          c['oracle_'+verdict] += 1
          if verdict=='parallel':
              c['global_false_serializations'] += 1
          write_only_parallel = (not stale) and (not ww)
          if write_only_parallel and verdict != 'parallel':
              c['write_only_unsafe_parallel'] += 1
    return c


def validate(result, expected=None):
    if expected is None:
        expected = independent_expected()
    e=[]
    if result.get('formal_invocations') != 1 or result.get('reruns') != 0 or result.get('resources') != 4:
        e.append('allocation')
    counts=result.get('counts',{})
    for key,val in expected.items():
        if counts.get(key) != val:
            e.append('count:'+key)
    for key in ('candidate_oracle_mismatch','candidate_stale_parallel','candidate_cross_rw_parallel','candidate_ww_parallel'):
        if counts.get(key) != 0:
            e.append('unsafe:'+key)
    if counts.get('global_false_serializations',0) <= 0:
        e.append('global_discriminator')
    if counts.get('write_only_unsafe_parallel',0) <= 0:
        e.append('write_only_discriminator')
    if not all(result.get('controls',{}).values()) or len(result.get('controls',{})) != 5:
        e.append('controls')
    w=result.get('witnesses',{})
    if set(w) != {'stale_read','a_write_b_read','b_write_a_read','ww'}:
        e.append('witnesses')
    if result.get('decision') != 'PASS_OPTIMISTIC_READWRITE_COMMIT_CRITERION_SCOPED' or result.get('pass') is not True:
        e.append('decision')
    return sorted(set(e))


def main():
    result=json.loads((ROOT/'RESULT.json').read_text())
    expected=independent_expected()
    errors=validate(result,expected)
    out={
      'pass':not errors,
      'errors':errors,
      'decision':result.get('decision') if not errors else 'FAIL_INTEGRITY',
      'expected_counts':expected,
      'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest(),
    }
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
    raise SystemExit(0 if not errors else 1)

if __name__=='__main__':
    main()
