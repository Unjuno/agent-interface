from __future__ import annotations
import json
from pathlib import Path
from model import brute_failure_phases, failure_phase_intervals, interval_cardinality
from oracle import closed_form_failure_count, guaranteed_boundary

ROOT = Path(__file__).resolve().parent


def run():
    combos = 0
    mismatches = []
    for period in range(2, 129):
        for attempts in range(2, 6):
            for span in range(1, period + 1):
                brute = len(brute_failure_phases(period, span, attempts))
                exact = interval_cardinality(failure_phase_intervals(period, span, attempts))
                closed = closed_form_failure_count(period, span, attempts)
                combos += 1
                if not (brute == exact == closed):
                    mismatches.append({
                        'period': period, 'attempts': attempts, 'span': span,
                        'brute': brute, 'exact': exact, 'closed': closed,
                    })
                    if len(mismatches) >= 20:
                        break
            if len(mismatches) >= 20:
                break
        if len(mismatches) >= 20:
            break

    invalid = 0
    for args in [(0,1,2),(10,0,2),(10,1,0),(10,-1,2)]:
        try:
            failure_phase_intervals(*args)
        except ValueError:
            invalid += 1

    directed = []
    for period in [7, 11, 29, 101]:
        for attempts in [2,3,4,5]:
            b = guaranteed_boundary(period, attempts)
            for span in sorted(set(x for x in [max(1,b-1), b, min(period,b+1), period] if 1 <= x <= period)):
                exact = interval_cardinality(failure_phase_intervals(period, span, attempts))
                closed = closed_form_failure_count(period, span, attempts)
                directed.append({'period':period,'attempts':attempts,'span':span,'exact':exact,'closed':closed})

    result = {
        'decision': 'PASS_CONSTRUCTION' if not mismatches and invalid == 4 else 'FAIL_CONSTRUCTION',
        'small_domain_combinations': combos,
        'mismatches': mismatches,
        'invalid_controls_rejected': invalid,
        'directed': directed,
    }
    (ROOT/'CONSTRUCTION.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))
    if result['decision'] != 'PASS_CONSTRUCTION':
        raise SystemExit(2)

if __name__ == '__main__':
    run()
