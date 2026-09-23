from __future__ import annotations
import json
from pathlib import Path
from model import candidate, global_serial, write_only, hazard_flags, PARALLEL, SERIALIZE, REVALIDATE
from oracle import oracle

ROOT = Path(__file__).resolve().parent
MASKS = range(16)

WITNESSES = {
    'stale_read': {
        'masks': {'ra': 1, 'wa': 0, 'rb': 0, 'wb': 0, 'changed': 1},
        'counterexample': 'A computes F(x)=x from prepared x=0; x changes to1 before commit.'
    },
    'a_write_b_read': {
        'masks': {'ra': 0, 'wa': 1, 'rb': 1, 'wb': 0, 'changed': 0},
        'counterexample': 'A writes x:=1 while B result is F_B(x)=x.'
    },
    'b_write_a_read': {
        'masks': {'ra': 2, 'wa': 0, 'rb': 0, 'wb': 2, 'changed': 0},
        'counterexample': 'B writes y:=1 while A result is F_A(y)=y.'
    },
    'ww': {
        'masks': {'ra': 0, 'wa': 4, 'rb': 0, 'wb': 4, 'changed': 0},
        'counterexample': 'A writes z:=0 and B writes z:=1; final value is order-dependent.'
    },
}


def main():
    counts = {
        'rows': 0,
        'candidate_oracle_mismatch': 0,
        'oracle_parallel': 0,
        'oracle_serialize': 0,
        'oracle_revalidate': 0,
        'candidate_stale_parallel': 0,
        'candidate_cross_rw_parallel': 0,
        'candidate_ww_parallel': 0,
        'global_false_serializations': 0,
        'write_only_unsafe_parallel': 0,
        'hazard_rows_stale_read': 0,
        'hazard_rows_a_write_b_read': 0,
        'hazard_rows_b_write_a_read': 0,
        'hazard_rows_ww': 0,
    }
    for ra in MASKS:
        for wa in MASKS:
            for rb in MASKS:
                for wb in MASKS:
                    for changed in MASKS:
                        counts['rows'] += 1
                        got = candidate(ra, wa, rb, wb, changed)
                        exp = oracle(ra, wa, rb, wb, changed)
                        if got != exp:
                            counts['candidate_oracle_mismatch'] += 1
                        counts['oracle_' + exp.lower()] += 1
                        hz = hazard_flags(ra, wa, rb, wb, changed)
                        for name, present in hz.items():
                            if present:
                                counts['hazard_rows_' + name] += 1
                        if got == PARALLEL and hz['stale_read']:
                            counts['candidate_stale_parallel'] += 1
                        if got == PARALLEL and (hz['a_write_b_read'] or hz['b_write_a_read']):
                            counts['candidate_cross_rw_parallel'] += 1
                        if got == PARALLEL and hz['ww']:
                            counts['candidate_ww_parallel'] += 1
                        if exp == PARALLEL and global_serial(ra,wa,rb,wb,changed) != PARALLEL:
                            counts['global_false_serializations'] += 1
                        wo = write_only(ra,wa,rb,wb,changed)
                        if wo == PARALLEL and exp != PARALLEL:
                            counts['write_only_unsafe_parallel'] += 1
    controls = {
        'same_surface_disjoint_parallel': candidate(1,2,4,8,0) == PARALLEL,
        'different_surface_shared_global_serial': candidate(0,8,8,0,0) == SERIALIZE,
        'read_read_overlap_parallel': candidate(1,2,1,4,0) == PARALLEL,
        'stale_read_revalidate': candidate(1,0,0,0,1) == REVALIDATE,
        'witnesses_present': set(WITNESSES) == {'stale_read','a_write_b_read','b_write_a_read','ww'},
    }
    passed = (
        counts['rows'] == 1_048_576 and
        counts['candidate_oracle_mismatch'] == 0 and
        counts['candidate_stale_parallel'] == 0 and
        counts['candidate_cross_rw_parallel'] == 0 and
        counts['candidate_ww_parallel'] == 0 and
        counts['global_false_serializations'] > 0 and
        counts['write_only_unsafe_parallel'] > 0 and
        all(controls.values())
    )
    out = {
        'task': 'OPTIMISTIC-CONCURRENT-READWRITE-COMMIT-R0-20260919-001',
        'formal_invocations': 1,
        'reruns': 0,
        'resources': 4,
        'counts': counts,
        'controls': controls,
        'witnesses': WITNESSES,
        'decision': 'PASS_OPTIMISTIC_READWRITE_COMMIT_CRITERION_SCOPED' if passed else 'FAIL_OPTIMISTIC_COMMIT_UNSOUND',
        'pass': passed,
    }
    (ROOT/'RESULT.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if passed else 1)

if __name__ == '__main__':
    main()
