"""Strict model proposal schema for one redaction-aware button task."""
import json


def parse(text):
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError('one JSON object required') from exc
    if type(value) is not dict or value.get('kind') not in ('click', 'stop'):
        raise ValueError('click or stop proposal required')
    if value['kind'] == 'click':
        if set(value) != {'kind', 'x', 'y', 'rationale'}:
            raise ValueError('exact click fields required')
        if (type(value['x']) is not int or type(value['y']) is not int or
                type(value['rationale']) is not str or
                not 1 <= len(value['rationale']) <= 300):
            raise ValueError('bounded integer click and rationale required')
    else:
        if set(value) != {'kind', 'reason'} or type(value['reason']) is not str or \
                not 1 <= len(value['reason']) <= 300:
            raise ValueError('bounded stop reason required')
    return value

