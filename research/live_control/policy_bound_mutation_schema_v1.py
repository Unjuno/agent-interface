"""Strict mutation proposal bound to observation and presentation policy."""
import json


def parse(text, *, expected_text, presented_binding):
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
    required = {'kind', 'observation_id', 'policy_id', 'policy_version',
                'field_x', 'field_y', 'save_x', 'save_y', 'text', 'rationale'}
    if set(value) != required:
        raise ValueError('exact policy-bound replacement fields required')
    for name in ('field_x', 'field_y', 'save_x', 'save_y', 'policy_version'):
        if type(value[name]) is not int:
            raise ValueError('integer coordinates/version required')
    if value['text'] != expected_text:
        raise ValueError('replacement text mismatch')
    binding = {name: value[name] for name in
               ('observation_id', 'policy_id', 'policy_version')}
    if binding != presented_binding:
        raise ValueError('proposal did not bind presented observation policy')
    if type(value['rationale']) is not str or not 1 <= len(value['rationale']) <= 300:
        raise ValueError('bounded rationale required')
    return value
