"""Opt-in receipt projection: exact duplicate event objects become local refs."""
import copy
import json


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def compact_receipt(view):
    if view.get('schema') != 'agent-interface/receipt-view-v1':
        raise ValueError('receipt-view-v1 required')
    result = copy.deepcopy(view)
    events = result['events']
    index = {}
    for number, event in enumerate(events):
        index.setdefault(_encoded(event), number)
    references = {}

    def visit(value, path):
        if isinstance(value, dict):
            target = index.get(_encoded(value))
            if target is not None:
                references[path] = target
                return {'event_ref': target}
            return {key: visit(child, path + '/' + key.replace('~', '~0').replace('/', '~1'))
                    for key, child in value.items()}
        if isinstance(value, list):
            return [visit(child, path + '/' + str(n)) for n, child in enumerate(value)]
        return value

    result['report'] = visit(result['report'], '/report')
    result['schema'] = 'agent-interface/receipt-view-v2-event-refs'
    result['event_references'] = references
    result['reference_scope'] = 'Only listed JSON-pointer paths are references to complete objects in events[index]. No external lookup. Raw source remains authoritative.'
    return result


def expand_receipt(view):
    """Reconstruct the original v1 view, interpreting only declared ref paths."""
    if view.get('schema') != 'agent-interface/receipt-view-v2-event-refs':
        raise ValueError('event-reference receipt required')
    result = copy.deepcopy(view)
    references = result.pop('event_references')
    result.pop('reference_scope')
    for path, number in references.items():
        if (not isinstance(path, str) or not (path == '/report' or path.startswith('/report/'))
                or type(number) is not int or not 0 <= number < len(result['events'])):
            raise ValueError('invalid event reference')
        parts = [part.replace('~1', '/').replace('~0', '~') for part in path.split('/')[1:]]
        parent = result
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        if parent[key] != {'event_ref': number}:
            raise ValueError('event reference marker mismatch')
        parent[key] = copy.deepcopy(result['events'][number])
    result['schema'] = 'agent-interface/receipt-view-v1'
    return result
