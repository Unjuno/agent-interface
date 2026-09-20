"""Opt-in receipt projection: exact duplicate event objects become local refs."""
import copy
import json

NATIVE_REFS = 'agent-interface/native-receipt-v1-observation-refs'
NATIVE_MULTI_REFS = 'agent-interface/native-receipt-v2-observation-refs'


def compact_native_receipt(view):
    """Choose the smallest lossless representation, including multi-capture refs."""
    if any(key in view for key in ('schema', 'observation_references', 'reference_scope')):
        return copy.deepcopy(view)  # Already projected or caller-owned metadata.
    candidates = [view, _compact_native_single(view), _compact_native_multiple(view)]
    return copy.deepcopy(min(candidates, key=lambda value: len(_encoded(value).encode('utf-8'))))


def _compact_native_multiple(view):
    result = copy.deepcopy(view)
    if not isinstance(result.get('native_result'), dict):
        return result
    references, canonical = {}, {}
    top = result['native_result'].get('observation')
    def is_observation(value):
        return isinstance(value, dict) and type(value.get('sequence')) is int and isinstance(value.get('native'), dict)
    if is_observation(top):
        canonical[_encoded(top)] = '/native_result/observation'
    def visit(value, path):
        if is_observation(value):
            identity = _encoded(value)
            target = canonical.setdefault(identity, path)
            if path != target:
                references[path] = target
                return {'observation_ref': target}
            return value  # Canonical observations stay complete, never nested refs.
        if isinstance(value, dict):
            return {key: visit(child, path+'/'+key.replace('~', '~0').replace('/', '~1'))
                    for key, child in value.items()}
        if isinstance(value, list):
            return [visit(child, path+'/'+str(index)) for index, child in enumerate(value)]
        return value
    result['native_result'] = visit(result['native_result'], '/native_result')
    result.update(schema=NATIVE_MULTI_REFS, observation_references=references,
        reference_scope='Only listed source JSON pointers are references. Each target is a complete observation in this response; all other reference-shaped values are literal.')
    return result


def _compact_native_single(view):
    """Reference exact copies of the explicit top-level native observation."""
    report = view.get('native_result', {})
    observation = report.get('observation')
    if not isinstance(observation, dict) or 'native' not in observation:
        return copy.deepcopy(view)
    result = copy.deepcopy(view)
    references = []
    canonical = _encoded(observation)

    def visit(value, path):
        if path == '/native_result/observation':
            return value
        if isinstance(value, dict):
            if _encoded(value) == canonical:
                references.append(path)
                return {'observation_ref': '/native_result/observation'}
            return {key: visit(child, path + '/' + key.replace('~', '~0').replace('/', '~1'))
                    for key, child in value.items()}
        if isinstance(value, list):
            return [visit(child, path + '/' + str(n)) for n, child in enumerate(value)]
        return value

    result['native_result'] = visit(result['native_result'], '/native_result')
    result['schema'] = NATIVE_REFS
    result['observation_references'] = references
    result['reference_scope'] = 'Only listed JSON-pointer paths refer to the complete native_result.observation in this response. Other reference-shaped values are literal.'
    # A small/no-duplicate report must not pay for reference bookkeeping.
    return result if len(_encoded(result).encode()) < len(_encoded(view).encode()) else copy.deepcopy(view)


def expand_native_receipt(view):
    if view.get('schema') == NATIVE_MULTI_REFS:
        return _expand_native_multiple(view)
    if view.get('schema') != NATIVE_REFS:
        if 'schema' not in view and 'native_result' in view:
            return copy.deepcopy(view)
        raise ValueError('native observation-reference receipt required')
    result = copy.deepcopy(view)
    result.pop('schema')
    references = result.pop('observation_references')
    result.pop('reference_scope')
    observation = result['native_result']['observation']
    if (not isinstance(references, list) or any(not isinstance(p, str) for p in references)
            or len(set(references)) != len(references)):
        raise ValueError('unique native reference paths required')
    for path in references:
        if (not isinstance(path, str) or not path.startswith('/native_result/')
                or path == '/native_result/observation' or path.startswith('/native_result/observation/')):
            raise ValueError('invalid native observation reference')
        parts = [part.replace('~1', '/').replace('~0', '~') for part in path.split('/')[1:]]
        parent = result
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        if parent[key] != {'observation_ref': '/native_result/observation'}:
            raise ValueError('native reference marker mismatch')
        parent[key] = copy.deepcopy(observation)
    return result


def _native_pointer(root, path):
    if not isinstance(path, str) or not path.startswith('/native_result/'):
        raise ValueError('native JSON pointer required')
    parts = path.split('/')[1:]
    for part in parts:
        remaining = part.replace('~0', '').replace('~1', '')
        if '~' in remaining:
            raise ValueError('invalid JSON pointer escape')
    parts = [part.replace('~1', '/').replace('~0', '~') for part in parts]
    parent = root
    for index, part in enumerate(parts):
        if isinstance(parent, list):
            if not part.isascii() or not part.isdigit() or str(int(part)) != part or int(part) >= len(parent):
                raise ValueError('invalid array reference')
            key = int(part)
        elif isinstance(parent, dict) and part in parent:
            key = part
        else:
            raise ValueError('reference path does not exist')
        if index == len(parts)-1:
            return parent, key
        parent = parent[key]


def _expand_native_multiple(view):
    result = copy.deepcopy(view)
    references = result.get('observation_references')
    if not isinstance(references, dict) or any(not isinstance(p, str) or not isinstance(t, str)
                                             for p, t in references.items()):
        raise ValueError('native reference map required')
    replacements = []
    for path, target in references.items():
        parent, key = _native_pointer(result, path)
        target_parent, target_key = _native_pointer(result, target)
        observation = target_parent[target_key]
        if (path == '/native_result/observation' or path.startswith('/native_result/observation/')
                or path == target or target in references
                or any(other.startswith(path+'/') or other.startswith(target+'/') for other in references)
                or not isinstance(observation, dict) or type(observation.get('sequence')) is not int
                or not isinstance(observation.get('native'), dict)
                or parent[key] != {'observation_ref': target}):
            raise ValueError('invalid, chained or overlapping native observation reference')
        replacements.append((parent, key, copy.deepcopy(observation)))
    for parent, key, observation in replacements:
        parent[key] = observation
    for field in ('schema', 'observation_references', 'reference_scope'):
        result.pop(field)
    return result


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
