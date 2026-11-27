"""Build read-only callbacks from a small, declarative exact-pixel profile."""
import math

from runtime.core_v1.compiled_gui import validate


def _point(value, name):
    if (type(value) is not list or len(value) != 2 or
            any(type(item) is not int or item < 0 for item in value)):
        raise ValueError(name + ' must be a nonnegative [x,y] integer point')
    return tuple(value)


def _rgb(value, name):
    if (type(value) is not list or len(value) != 3 or
            any(type(item) is not int or not 0 <= item <= 255 for item in value)):
        raise ValueError(name + ' must be an [r,g,b] byte triple')
    return tuple(value)


def _scalar(value):
    if type(value) not in (bool, int, float, str):
        return False
    return not (type(value) is float and not math.isfinite(value))


def build_callbacks(interface, predicate_rules, effect_rules):
    """Return bounded read-only pixel callbacks for one validated interface.

    This is a perception aid only. Pixel matches are not independent task
    scoring, authenticated application state, or proof of durable effects.
    """
    spec = validate(interface)
    if type(predicate_rules) is not dict or set(predicate_rules) != set(spec['predicates']):
        raise ValueError('one exact pixel rule per declared predicate required')
    predicates = {}
    for name, rule in predicate_rules.items():
        if (type(rule) is not dict or set(rule) != {'point','states'} or
                type(rule['states']) is not list or not 1 <= len(rule['states']) <= 16):
            raise ValueError('predicate rule requires a point and 1..16 RGB states')
        point = _point(rule['point'],'predicate point')
        states = {}
        for state in rule['states']:
            if type(state) is not dict or set(state) != {'rgb','value'} or not _scalar(state['value']):
                raise ValueError('pixel state requires exact RGB and scalar value')
            rgb = _rgb(state['rgb'],'state RGB')
            if rgb in states:
                raise ValueError('duplicate RGB state')
            states[rgb] = state['value']
        predicates[name] = (point, states)

    actions = set(spec['actions'])
    if type(effect_rules) is not dict or set(effect_rules) != actions:
        raise ValueError('one exact pixel effect rule per declared action required')
    effects = {}
    for name, rule in effect_rules.items():
        if type(rule) is not dict or set(rule) != {'point','rgb'}:
            raise ValueError('effect rule requires exactly point and RGB')
        effects[name] = (_point(rule['point'],'effect point'),_rgb(rule['rgb'],'effect RGB'))

    def perceive(native, image):
        del native
        values = {}
        for name, (point, states) in predicates.items():
            x,y = point
            values[name] = states.get(image.getpixel((x,y))) if x < image.width and y < image.height else None
            if values[name] is None:
                values[name] = 'unknown'
        return values

    def verify_effect(payload, native, image):
        del native
        rule = effects.get(payload.get('action'))
        if rule is None:
            status = 'unavailable'
        else:
            point, expected = rule
            x,y = point
            status = ('succeeded' if x < image.width and y < image.height
                      and image.getpixel((x,y)) == expected else 'unavailable')
        return {'status':status,
                'evidence_ref':payload['observation']['evidence_ref']}

    return perceive, verify_effect
