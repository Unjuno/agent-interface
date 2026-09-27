from __future__ import annotations
import itertools

FAMILIES = [
    'SUCCEEDED', 'IN_PROGRESS', 'BLOCKED', 'AUTHORITY_REQUIRED',
    'TARGET_NOT_FOUND', 'CAPABILITY_UNSUPPORTED', 'CONFLICT',
    'IMPOSSIBLE_UNDER_CONSTRAINTS', 'FAILED_UNKNOWN',
]

COARSE = {
    'SUCCEEDED': ('ok', False),
    'IN_PROGRESS': ('pending', False),
    'BLOCKED': ('error', False),
    'AUTHORITY_REQUIRED': ('error', False),
    'TARGET_NOT_FOUND': ('error', True),
    'CAPABILITY_UNSUPPORTED': ('error', False),
    'CONFLICT': ('error', False),
    'IMPOSSIBLE_UNDER_CONSTRAINTS': ('error', True),
    'FAILED_UNKNOWN': ('error', False),
}


def build_rows():
    rows=[]
    idx=0
    for family, freshness, completeness, retry_context, rep in itertools.product(
        FAMILIES,
        ['CURRENT','STALE'],
        ['COMPLETE','INCOMPLETE'],
        ['IDENTICAL_RETRY_VALID','REQUIRES_CHANGE'],
        range(2),
    ):
        status, timeout = COARSE[family]
        rows.append({
            'row_id': f'r{idx:03d}',
            'family': family,
            'freshness': freshness,
            'completeness': completeness,
            'retry_context': retry_context,
            'coarse_status': status,
            'timeout': timeout,
            'rep': rep,
            'evidence_ref': f'evidence:{idx:03d}',
        })
        idx += 1
    return rows
