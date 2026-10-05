"""Strict read/unknown response schema for the redaction observation experiment."""
import json


def parse(text):
    value = json.loads(text)
    if type(value) is not dict or type(value.get('rationale')) is not str or not 1 <= len(value['rationale']) <= 256:
        raise ValueError('bounded response with rationale required')
    if value.get('status') == 'READABLE':
        if set(value) != {'status', 'value', 'rationale'}:
            raise ValueError('exact readable response required')
        if type(value['value']) is not str or not 1 <= len(value['value']) <= 128:
            raise ValueError('bounded readable value required')
    elif value.get('status') == 'UNKNOWN':
        if set(value) != {'status', 'reason', 'rationale'} or value.get('reason') not in {
                'REDACTED_BY_POLICY', 'NOT_OBSERVED', 'OCCLUDED', 'CAPTURE_FAILED'}:
            raise ValueError('typed unknown response required')
    else:
        raise ValueError('status must be READABLE or UNKNOWN')
    return value
