"""Expand explicit bounded key repetitions; never schedule or dispatch input."""
from copy import deepcopy


def expand_key_repeats(operations, *, max_ops):
    if type(max_ops) is not int or not 0 <= max_ops <= 128:
        raise ValueError('operation capacity must be 0..128')
    result = []
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError('operation must be an object')
        count = operation.get('repeat', 1)
        if 'repeat' in operation and operation.get('op') != 'key_chord':
            raise ValueError('repeat is supported only for key_chord')
        if type(count) is not int or not 1 <= count <= 126:
            raise ValueError('repeat must be an integer in 1..126')
        if len(result) + count > max_ops:
            raise ValueError('expanded operations exceed program capacity')
        item = {k: v for k, v in operation.items() if k != 'repeat'}
        result.extend(deepcopy(item) for _ in range(count))
    return result


def expand_text_gaps(operations, *, max_ops=128):
    """Compile explicit text gaps and key repeats, retaining source positions."""
    if type(max_ops) is not int or not 0 <= max_ops <= 128:
        raise ValueError('operation capacity must be 0..128')
    result, sources = [], []
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise ValueError('operation must be an object')
        if 'gap_ms' not in operation:
            expanded = expand_key_repeats([operation], max_ops=max_ops-len(result))
            result.extend(expanded)
            sources.extend({'source_operation_index': index, 'expanded_occurrence': i+1}
                           for i in range(len(expanded)))
            continue
        gap, value = operation['gap_ms'], operation.get('text')
        if (operation.get('op') != 'text' or 'repeat' in operation or
                type(gap) is not int or not 0 <= gap <= 1000 or
                not isinstance(value, str) or len(value) > 16384):
            raise ValueError('gap_ms requires text and an integer in 0..1000; repeat is not allowed')
        count = max(1, 2*len(value)-1) if gap else 1
        if len(result)+count > max_ops:
            raise ValueError('expanded operations exceed program capacity')
        item = {k: deepcopy(v) for k,v in operation.items() if k != 'gap_ms'}
        if not gap or not value:
            result.append(item)
            sources.append({'source_operation_index': index, 'character_index': None, 'phase': 'text'})
            continue
        for char_index, character in enumerate(value):
            if char_index:
                result.append({'op': 'wait_update', 'timeout_ms': gap})
                sources.append({'source_operation_index': index, 'character_index': char_index, 'phase': 'gap_before_character'})
            result.append(dict(item, text=character))
            sources.append({'source_operation_index': index, 'character_index': char_index, 'phase': 'text'})
    return result, sources
