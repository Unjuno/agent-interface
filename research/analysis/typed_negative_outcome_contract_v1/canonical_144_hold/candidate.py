from __future__ import annotations

LABELS = {
    'SUCCEEDED', 'IN_PROGRESS', 'BLOCKED', 'AUTHORITY_REQUIRED',
    'TARGET_NOT_FOUND', 'CAPABILITY_UNSUPPORTED', 'CONFLICT',
    'IMPOSSIBLE_UNDER_CONSTRAINTS', 'FAILED_UNKNOWN',
}

REQ = {
    'SUCCEEDED': 'NONE',
    'IN_PROGRESS': 'WAIT',
    'BLOCKED': 'WAIT_OR_RETRY',
    'AUTHORITY_REQUIRED': 'ACQUIRE_AUTHORITY',
    'TARGET_NOT_FOUND': 'NEW_OBSERVATION_OR_TARGET',
    'CAPABILITY_UNSUPPORTED': 'SELECT_DECLARED_FALLBACK',
    'CONFLICT': 'REFRESH_STATE',
    'IMPOSSIBLE_UNDER_CONSTRAINTS': 'REPLAN_CONSTRAINTS',
    'FAILED_UNKNOWN': 'NEW_OBSERVATION',
}


def classify(row: dict) -> dict:
    if row['freshness'] != 'CURRENT' or row['completeness'] != 'COMPLETE':
        label = 'FAILED_UNKNOWN'
        retry = False
        required = 'NEW_OBSERVATION'
    else:
        label = row['family']
        if label not in LABELS:
            raise ValueError('UNKNOWN_FAMILY')
        retry = label == 'BLOCKED' and row['retry_context'] == 'IDENTICAL_RETRY_VALID'
        required = REQ[label]
    return {
        'label': label,
        'identical_retry_allowed': retry,
        'required_change': required,
        'authority_granted': False,
    }


def coarse_compare(row: dict) -> dict:
    # Intentionally incomplete comparator: sees only coarse status + timeout.
    status = row['coarse_status']
    if status == 'ok':
        label, retry, required = 'SUCCEEDED', False, 'NONE'
    elif status == 'pending':
        label, retry, required = 'IN_PROGRESS', False, 'WAIT'
    elif row['timeout']:
        label, retry, required = 'IMPOSSIBLE_UNDER_CONSTRAINTS', False, 'REPLAN_CONSTRAINTS'
    else:
        label, retry, required = 'BLOCKED', True, 'WAIT_OR_RETRY'
    return {
        'label': label,
        'identical_retry_allowed': retry,
        'required_change': required,
        'authority_granted': False,
    }
