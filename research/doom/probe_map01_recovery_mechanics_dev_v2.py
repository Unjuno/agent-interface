"""Development v2: repair retained-input attribution only; runtime semantics remain v1."""
from __future__ import annotations
from collections import Counter
import probe_map01_recovery_mechanics_dev_v1 as v1


def direct_bounds(events, program_id):
    """Pair id-less admissions to this program's verified release batch."""
    releases = [r for r in events
                if r.get('event') == 'input_release_transition'
                and r.get('release_batch_identifier') == program_id]
    if not releases:
        return {'measurement_ready': True, 'hold_count': 0,
                'retained_lower_ms': 0.0, 'retained_upper_ms': 0.0,
                'censor_width_ms': 0.0}
    if any(r.get('owner_transition_verified') is not True for r in releases):
        raise AssertionError('unverified release transition')
    release_keys = [(r.get('intent_token'), r.get('key')) for r in releases]
    if any(t is None or k is None for t, k in release_keys):
        raise AssertionError('release transition lacks intent/key')
    if len(set(release_keys)) != len(release_keys):
        raise AssertionError('duplicate release intent/key')
    wanted = set(release_keys)
    admissions = [r for r in events
                  if r.get('event') == 'input_admission'
                  and (r.get('intent_token'), r.get('key')) in wanted]
    admission_keys = [(r.get('intent_token'), r.get('key')) for r in admissions]
    if Counter(admission_keys) != Counter(release_keys):
        raise AssertionError('admission/release identity mismatch')
    by_release = {(r['intent_token'], r['key']): r for r in releases}
    lower = upper = 0
    widths = []
    for a in admissions:
        rel = by_release[(a['intent_token'], a['key'])]
        for field in ('admitted_ns', 'input_ack_ns'):
            if type(a.get(field)) is not int:
                raise AssertionError('admission timestamp missing')
        for field in ('release_call_started_ns', 'release_call_returned_ns'):
            if type(rel.get(field)) is not int:
                raise AssertionError('release timestamp missing')
        lo = rel['release_call_started_ns'] - a['input_ack_ns']
        hi = rel['release_call_returned_ns'] - a['admitted_ns']
        if not 0 <= lo <= hi:
            raise AssertionError('invalid retained-input interval')
        lower += lo; upper += hi; widths.append(hi-lo)
    return {'measurement_ready': True, 'hold_count': len(admissions),
            'retained_lower_ms': lower / 1e6,
            'retained_upper_ms': upper / 1e6,
            'censor_width_ms': sum(widths) / 1e6}


if __name__ == '__main__':
    v1.direct_bounds = direct_bounds
    v1.main()
