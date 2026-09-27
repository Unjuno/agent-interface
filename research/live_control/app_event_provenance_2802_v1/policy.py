from __future__ import annotations

PENDING='PENDING'
SATISFIED='SATISFIED'
EXPIRED='EXPIRED'
UNKNOWN_SOURCE='UNKNOWN_SOURCE'
UNKNOWN_CLOCK_DOMAIN='UNKNOWN_CLOCK_DOMAIN'
UNKNOWN_GAP='UNKNOWN_GAP'
UNKNOWN_ORDER='UNKNOWN_ORDER'
UNKNOWN_TIME='UNKNOWN_TIME'
TERMINAL={SATISFIED,EXPIRED,UNKNOWN_SOURCE,UNKNOWN_CLOCK_DOMAIN,UNKNOWN_GAP,UNKNOWN_ORDER,UNKNOWN_TIME}


def candidate(events, bound_ns:int):
    anchor=None
    current=None
    for e in events:
        if anchor is None:
            if e['label']!='A':
                continue
            anchor=e
            current=e
            continue
        if e['source_id'] != anchor['source_id']:
            return UNKNOWN_SOURCE
        if e['clock_domain'] != anchor['clock_domain']:
            return UNKNOWN_CLOCK_DOMAIN
        if e['seq'] <= current['seq']:
            return UNKNOWN_ORDER
        if e['seq'] != current['seq'] + 1:
            return UNKNOWN_GAP
        if e['t_ns'] < current['t_ns']:
            return UNKNOWN_TIME
        if e['t_ns'] - anchor['t_ns'] > bound_ns:
            return EXPIRED
        current=e
        if e['label']=='B':
            return SATISFIED
    return PENDING


def unsafe_timestamp_only(events, bound_ns:int):
    anchor=None
    last_t=None
    for e in events:
        t=e['t_ns']
        if last_t is not None and t < last_t:
            return UNKNOWN_TIME
        last_t=t
        if anchor is None:
            if e['label']=='A':
                anchor=e
            continue
        if t-anchor['t_ns'] > bound_ns:
            return EXPIRED
        if e['label']=='B':
            return SATISFIED
    return PENDING
