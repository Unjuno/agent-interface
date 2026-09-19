from __future__ import annotations

PROVEN_COMPLETE='PROVEN_COMPLETE'
PARTIAL='PARTIAL'
UNKNOWN='UNKNOWN'


def required_decision(true_relevance:set[int], critical:set[int], changed:set[int])->str:
    return 'FORWARD' if (changed & true_relevance or changed & critical) else 'SUPPRESS'


def assume_complete(declared:set[int], critical:set[int], changed:set[int], current:bool=True)->str:
    if not current:
        return 'FORWARD_FULL_CURRENT'
    return 'FORWARD' if (changed & declared or changed & critical) else 'SUPPRESS'


def complete_only(declared:set[int], critical:set[int], changed:set[int], coverage:str, current:bool=True)->str:
    if not current:
        return 'FORWARD_FULL_CURRENT'
    if coverage not in (PROVEN_COMPLETE,PARTIAL,UNKNOWN):
        raise ValueError('bad_coverage')
    if coverage != PROVEN_COMPLETE:
        return 'FORWARD_FULL_CURRENT'
    return 'FORWARD' if (changed & declared or changed & critical) else 'SUPPRESS'
