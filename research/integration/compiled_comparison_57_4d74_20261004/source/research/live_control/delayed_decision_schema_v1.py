"""Bounded decisions for the delayed-effect fixed-image comparison."""
import json


def parse(text, token):
    value = json.loads(text)
    if type(value) is not dict or value.get('kind') not in ('wait_and_check', 'submit_once', 'verify'):
        raise ValueError('bounded delayed-effect decision required')
    if type(value.get('rationale')) is not str or not 1 <= len(value['rationale']) <= 600:
        raise ValueError('bounded rationale required')
    if value['kind'] == 'wait_and_check':
        if set(value) != {'kind', 'delay_ms', 'rationale'} or type(value['delay_ms']) is not int:
            raise ValueError('wait decision fields required')
        if not 1000 <= value['delay_ms'] <= 6000:
            raise ValueError('wait outside effect window')
    elif value['kind'] == 'submit_once':
        if set(value) != {'kind', 'steps', 'rationale'} or type(value['steps']) is not list:
            raise ValueError('submit decision fields required')
        steps = value['steps']
        allowed = [
            {'op': 'pointer_click', 'x': 150, 'y': 277, 'duration_ms': 80},
            {'op': 'chord', 'modifier': 'Control_L', 'key': 'a'},
            {'op': 'text', 'text': token},
            {'op': 'key', 'key': 'Return'},
        ]
        if steps != allowed:
            raise ValueError('exact single submission program required')
    elif set(value) != {'kind', 'rationale'}:
        raise ValueError('verify decision fields required')
    return value

