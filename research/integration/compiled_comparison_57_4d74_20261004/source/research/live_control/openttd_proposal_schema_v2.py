"""Strict OpenTTD schema with full-screen coordinates and hover probing."""
import json


def parse(text):
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError('one JSON object required') from exc
    if type(value) is not dict or value.get('kind') not in ('act', 'verify', 'stop'):
        raise ValueError('act, verify or stop required')
    if value['kind'] == 'stop':
        if set(value) != {'kind', 'rationale'}:
            raise ValueError('exact stop fields required')
    elif value['kind'] == 'verify':
        if set(value) != {'kind', 'road_visible', 'rationale'} or \
                type(value['road_visible']) is not bool:
            raise ValueError('exact visual verification required')
    else:
        if set(value) != {'kind', 'steps', 'rationale'} or \
                type(value['steps']) is not list or not 1 <= len(value['steps']) <= 6:
            raise ValueError('1..6 exact action steps required')
        for step in value['steps']:
            if type(step) is not dict or step.get('op') not in (
                    'pointer_move', 'pointer_click', 'pointer_drag', 'observe'):
                raise ValueError('pointer move, click, drag or observe required')
            if step['op'] == 'observe':
                if set(step) != {'op'}:
                    raise ValueError('exact observe required')
            elif step['op'] in ('pointer_move', 'pointer_click'):
                if set(step) != {'op', 'x', 'y'} or any(
                        type(step.get(name)) is not int for name in ('x', 'y')):
                    raise ValueError('exact integer click required')
            else:
                if set(step) != {'op', 'points', 'duration_ms'} or \
                        type(step['duration_ms']) is not int or \
                        not 80 <= step['duration_ms'] <= 1000 or \
                        type(step['points']) is not list or not 2 <= len(step['points']) <= 8:
                    raise ValueError('bounded drag required')
                for point in step['points']:
                    if type(point) is not dict or set(point) != {'x', 'y'} or \
                            any(type(point.get(name)) is not int for name in ('x', 'y')):
                        raise ValueError('exact drag point required')
            coordinates = ([step] if step['op'] in ('pointer_move', 'pointer_click') else
                           step.get('points', []))
            if any(not 0 <= point['x'] < 1280 or not 0 <= point['y'] < 800
                   for point in coordinates):
                raise ValueError('point outside OpenTTD surface')
    if type(value.get('rationale')) is not str or not 1 <= len(value['rationale']) <= 600:
        raise ValueError('bounded rationale required')
    return value
