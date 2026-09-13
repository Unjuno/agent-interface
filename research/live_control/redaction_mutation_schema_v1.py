"""Strict proposal schema for editing a field that may be policy-redacted."""
import json


def parse(text, expected_text):
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError('one JSON object required') from exc
    if type(value) is not dict or value.get('kind') not in ('replace_and_save', 'stop'):
        raise ValueError('replace_and_save or stop required')
    if value['kind'] == 'stop':
        if set(value) != {'kind', 'reason'} or type(value['reason']) is not str or \
                not 1 <= len(value['reason']) <= 300:
            raise ValueError('bounded stop reason required')
        return value
    if set(value) != {'kind', 'field_x', 'field_y', 'save_x', 'save_y',
                      'text', 'rationale'}:
        raise ValueError('exact replace fields required')
    for name in ('field_x', 'field_y', 'save_x', 'save_y'):
        if type(value[name]) is not int:
            raise ValueError('integer coordinates required')
    if value['text'] != expected_text:
        raise ValueError('replacement text mismatch')
    if type(value['rationale']) is not str or not 1 <= len(value['rationale']) <= 300:
        raise ValueError('bounded rationale required')
    return value
