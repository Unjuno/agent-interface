"""Bounded model proposals for a declared local form value; no text coercion."""
import json


def validate(value, expected_text):
    if (type(expected_text) is not str or not 1 <= len(expected_text) <= 128 or
            not expected_text.isascii() or not expected_text.isalnum()):
        raise ValueError('bounded alphanumeric task text required')
    if type(value) is not dict:
        raise ValueError('object required')
    if type(value.get('rationale')) is not str or not 1 <= len(value['rationale']) <= 600:
        raise ValueError('bounded rationale required')
    kind = value.get('kind')
    if kind == 'verify':
        if (set(value) != {'kind', 'rationale', 'submission_received_visible'} or
                type(value['submission_received_visible']) is not bool):
            raise ValueError('visible submission fields required')
    elif kind == 'stop':
        if set(value) != {'kind', 'rationale'}:
            raise ValueError('stop fields')
    elif kind == 'act':
        if set(value) != {'kind', 'rationale', 'steps'}:
            raise ValueError('act fields')
        steps = value['steps']
        if type(steps) is not list or not 1 <= len(steps) <= 10:
            raise ValueError('bounded steps required')
        for step in steps:
            if type(step) is not dict:
                raise ValueError('step object required')
            op = step.get('op')
            if op == 'text':
                if set(step) != {'op', 'text'} or step['text'] != expected_text:
                    raise ValueError('text must equal the declared task value')
            elif op == 'key':
                if set(step) != {'op', 'key'} or step['key'] not in ('Return', 'Tab', 'Escape'):
                    raise ValueError('unsupported key')
            elif op == 'chord':
                if set(step) != {'op', 'modifier', 'key'} or (step['modifier'], step['key']) != ('Control_L', 'a'):
                    raise ValueError('only select-all chord supported')
            elif op == 'pointer_click':
                if (set(step) != {'op', 'x', 'y', 'duration_ms'} or
                        type(step['x']) is not int or type(step['y']) is not int or
                        not 0 <= step['x'] < 1280 or not 0 <= step['y'] < 800 or
                        type(step['duration_ms']) is not int or step['duration_ms'] != 80):
                    raise ValueError('bounded pointer required')
            else:
                raise ValueError('unsupported step')
    else:
        raise ValueError('unknown kind')
    return value


def parse(raw, expected_text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return validate(json.loads(raw, object_pairs_hook=unique), expected_text)
